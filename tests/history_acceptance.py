"""Run with the repository mounted read-only at /checks; only UUID test DBs are written."""

import os
import runpy
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlencode
from unittest.mock import patch
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException
from pymongo.collection import Collection
from pymongo.errors import AutoReconnect

from backend.audit import make_event, publish_pending, snapshot, update_with_events
from backend.db import connect, initialize_database
from backend.main import register_message
from backend.schemas import MessageInput
from backend.auth import UserIdentity

helpers = runpy.run_path(str(Path(__file__).with_name("compose_acceptance.py")))
call = helpers["call"]
MESSAGES = helpers["MESSAGES"]
AUDIT = helpers["AUDIT"]


def events(token, message_id, **filters):
    return call(AUDIT + "?" + urlencode({"messageId": message_id, "limit": 100, **filters}),
                200, token=token)["items"]


def verify_api(db, operator, admin):
    original = call(MESSAGES, 201, token=operator, body=helpers["INVOICE"])
    mid = original["id"]
    first_events = events(admin, mid)
    assert len(first_events) == 3
    assert all(event["source"] == "HISTORICAL" for event in first_events)
    assert db.audit_events.count_documents({"messageId": mid}) == 3
    original_events = list(db.audit_events.find({"messageId": mid}))

    for department in ("VENTAS", "RECURSOS_HUMANOS", "FACTURACION"):
        detail = call(f"{MESSAGES}/{mid}/classification", 200, token=operator, method="PATCH",
                      body={"department": department, "reason": f"Corregir destino a {department}"})
        assert detail["prediction"] == original["prediction"]
        assert detail["status"] == "EN_GESTION" and detail["assignmentOrigin"] == "MANUAL"
        assert detail["assignment"]["department"] == department

    history = events(admin, mid)
    manual = sorted((e for e in history if e["action"] == "CLASIFICACION_MANUAL"), key=lambda e: e["createdAt"])
    assert len(manual) == 3 and len({e["id"] for e in manual}) == 3
    assert manual[0]["before"]["department"] == "FACTURACION"
    assert manual[1]["before"]["department"] == "VENTAS"
    assert manual[2]["before"]["department"] == "RECURSOS_HUMANOS"
    assert all(e["after"]["prediction"] == original["prediction"] for e in manual)
    assert all(e["actorType"] == "USUARIO" and e["reason"] for e in manual)
    assert all(db.audit_events.find_one({"_id": e["_id"]}) == e for e in original_events)
    assert not any(k in db.messages.find_one({"_id": ObjectId(mid)})
                   for k in ("creationEvent", "manualEvent", "classificationEvent"))

    # Invalid operations create neither partial state changes nor events.
    before = db.messages.find_one({"_id": ObjectId(mid)})
    count = db.audit_events.count_documents({})
    for payload in ({"department": "VENTAS", "reason": " "}, {"department": "OTRO", "reason": "Motivo válido"}):
        call(f"{MESSAGES}/{mid}/classification", 422, token=operator, method="PATCH", body=payload)
    assert db.messages.find_one({"_id": ObjectId(mid)}) == before
    assert db.audit_events.count_documents({}) == count

    saved = call(f"{MESSAGES}/{mid}", 200, token=operator)
    params = {"text": "factura", "status": "EN_GESTION", "department": "FACTURACION",
              "dateFrom": saved["createdAt"], "dateTo": saved["createdAt"], "pageSize": 1}
    listing = call(MESSAGES + "?" + urlencode(params), 200, token=operator)
    assert listing["total"] == 1 and listing["items"][0]["id"] == mid
    assert not call(MESSAGES + "?" + urlencode({**params, "page": 2}), 200, token=operator)["items"]
    assert not call(MESSAGES + "?" + urlencode({**params, "department": "VENTAS"}),
                    200, token=operator)["items"]
    for query in ("status=OTRO", "department=OTRO", "dateFrom=ayer", "dateFrom=2026-01-01T00:00:00",
                  "dateFrom=2026-02-01T00:00:00Z&dateTo=2026-01-01T00:00:00Z"):
        call(MESSAGES + "?" + query, 422, token=operator)
    selected = events(admin, mid, actor="operador_historia", action="CLASIFICACION_MANUAL",
                      dateFrom=manual[1]["createdAt"], dateTo=manual[1]["createdAt"])
    assert len(selected) == 1 and selected[0]["id"] == manual[1]["id"]
    assert not events(admin, mid, actor="nadie", action="CLASIFICACION_MANUAL")
    call(AUDIT, 401)
    call(AUDIT, 403, token=operator)
    call(AUDIT, 405, token=admin, method="POST", body={"action": "NO_PERMITIDA"})
    call(AUDIT, 405, token=admin, method="DELETE")
    call(AUDIT + "?dateFrom=2026-02-01T00:00:00Z&dateTo=2026-01-01T00:00:00Z", 422, token=admin)
    call(f"{MESSAGES}/{mid}/classification", 401, method="PATCH",
         body={"department": "VENTAS", "reason": "Sin autorización"})
    call(f"{MESSAGES}/{mid}/status", 200, token=operator, method="PATCH",
         body={"status": "CERRADO", "reason": "Atención completada correctamente"})
    call(f"{MESSAGES}/{mid}/classification", 409, token=operator, method="PATCH",
         body={"department": "VENTAS", "reason": "No se puede tras el cierre"})
    assert len(events(admin, mid)) == 7

    # Embedded history remains untouched and can coexist with new events on the same message.
    now = datetime.now(timezone.utc)
    legacy_id = ObjectId()
    embedded = {"action": "CLASIFICACION_MANUAL", "actorUserId": "operador_historia",
                "messageId": str(legacy_id), "createdAt": now, "reason": "Motivo anterior"}
    db.messages.insert_one({"_id": legacy_id, "subject": "Mensaje legado", "body": "Contenido de prueba legado",
                            "status": "EN_GESTION", "department": "VENTAS", "prediction": None,
                            "createdBy": "operador_historia", "createdAt": now, "manualEvent": embedded})
    call(f"{MESSAGES}/{legacy_id}/classification", 200, token=operator, method="PATCH",
         body={"department": "FACTURACION", "reason": "Nueva corrección sobre legado"})
    mixed = events(admin, str(legacy_id), actor="operador_historia", action="CLASIFICACION_MANUAL")
    assert len(mixed) == 2 and {e["source"] for e in mixed} == {"LEGACY", "HISTORICAL"}
    assert next(e for e in mixed if e["source"] == "LEGACY")["before"] is None
    assert db.messages.find_one({"_id": legacy_id})["manualEvent"]["reason"] == embedded["reason"]
    assert db.audit_events.count_documents({"messageId": str(legacy_id)}) == 1
    legacy_filtered = events(
        admin, str(legacy_id), actor="operador_historia", action="CLASIFICACION_MANUAL",
        dateFrom=next(e["createdAt"] for e in mixed if e["source"] == "LEGACY"),
        dateTo=next(e["createdAt"] for e in mixed if e["source"] == "LEGACY"),
    )
    assert len(legacy_filtered) == 1 and legacy_filtered[0]["source"] == "LEGACY"


def verify_recovery_and_order(db):
    user = UserIdentity(id="operador_historia", role="OPERADOR")
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db, routing_threshold=0.45)))

    def infer_after_creation(subject, body):
        saved = db.messages.find_one({"subject": subject})
        assert saved["status"] == "RECIBIDO"
        assert db.audit_events.count_documents({"messageId": str(saved["_id"]), "action": "MENSAJE_REGISTRADO"}) == 1
        return None

    with patch("backend.main.classify", side_effect=infer_after_creation):
        result = register_message(MessageInput(subject="Orden comprobado", body="Contenido ficticio sin IA"), request, user)
    mid = ObjectId(result.id)
    before = db.messages.find_one({"_id": mid})
    changes = {"status": "EN_GESTION", "department": "VENTAS", "assignmentOrigin": "MANUAL"}
    event = make_event(mid, "CLASIFICACION_MANUAL", user.id, snapshot(before), snapshot({**before, **changes}), "Motivo de prueba")
    real_insert = Collection.insert_one

    def fail_audit(collection, document, *args, **kwargs):
        if collection.name == "audit_events":
            raise AutoReconnect("fallo simulado")
        return real_insert(collection, document, *args, **kwargs)

    with patch.object(Collection, "insert_one", fail_audit):
        try:
            update_with_events(db, before, changes, [event])
        except AutoReconnect:
            pass
        else:
            raise AssertionError("No se simuló el fallo de publicación")
    assert db.messages.find_one({"_id": mid})["pendingAudit"]
    publish_pending(db, mid)
    assert not db.messages.find_one({"_id": mid})["pendingAudit"]
    assert db.audit_events.count_documents({"_id": event["_id"]}) == 1
    # Retry after insertion but before acknowledgement must not duplicate/modify the event.
    db.messages.update_one({"_id": mid}, {"$push": {"pendingAudit": db.audit_events.find_one({"_id": event["_id"]})}})
    publish_pending(db, mid)
    publish_pending(db, mid)
    assert db.audit_events.count_documents({"_id": event["_id"]}) == 1
    try:
        update_with_events(db, before, changes, [event])
    except HTTPException as exc:
        assert exc.status_code == 409
    else:
        raise AssertionError("Una versión obsoleta modificó el mensaje")

    current = db.messages.find_one({"_id": mid})
    def compete(department):
        updates = {"department": department}
        concurrent_event = make_event(
            mid, "CLASIFICACION_MANUAL", user.id, snapshot(current),
            snapshot({**current, **updates}), "Corrección concurrente de prueba",
        )
        try:
            update_with_events(db, current, updates, [concurrent_event])
            return 200
        except HTTPException as exc:
            return exc.status_code
    count = db.audit_events.count_documents({"messageId": str(mid)})
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(compete, ("FACTURACION", "VENTAS", "RECURSOS_HUMANOS")))
    assert results.count(200) == 1 and results.count(409) == 2
    assert db.audit_events.count_documents({"messageId": str(mid)}) == count + 1
    # Leave an unpublished intent to prove the lifespan recovers it without migration.
    startup_event = make_event(
        mid, "CLASIFICACION_MANUAL", user.id, snapshot(current),
        snapshot(db.messages.find_one({"_id": mid})), "Reintento al iniciar",
    )
    db.messages.update_one({"_id": mid}, {"$push": {"pendingAudit": startup_event}})
    return startup_event["_id"]


def main():
    with connect() as client:
        name = "history_acceptance_" + uuid4().hex
        db = client[name]
        try:
            initialize_database(db)
            operator_credentials = helpers["create_fixture_user"](db, "operador_historia", "OPERADOR")
            admin_credentials = helpers["create_fixture_user"](db, "admin_historia", "ADMINISTRADOR")
            pending_id = verify_recovery_and_order(db)
            with helpers["start_api"](name, os.environ["AI_SERVICE_URL"]):
                assert db.audit_events.count_documents({"_id": pending_id}) == 1
                assert db.messages.count_documents({"pendingAudit.0": {"$exists": True}}) == 0
                operator = call(helpers["LOGIN"], 200, body=operator_credentials)["accessToken"]
                admin = call(helpers["LOGIN"], 200, body=admin_credentials)["accessToken"]
                verify_api(db, operator, admin)
            with helpers["start_api"](name, "http://127.0.0.1:1"):
                unclassified = call(MESSAGES, 201, token=operator, body=helpers["INVOICE"])
                assert unclassified["status"] == "PENDIENTE_CLASIFICACION"
                for department in ("VENTAS", "FACTURACION"):
                    changed = call(
                        f"{MESSAGES}/{unclassified['id']}/classification", 200, token=operator,
                        method="PATCH", body={"department": department, "reason": "Asignación sin predicción IA"},
                    )
                    assert changed["prediction"] is None and changed["assignmentOrigin"] == "MANUAL"
                assert len(events(admin, unclassified["id"], action="CLASIFICACION_MANUAL")) == 2
            print("Historia, correcciones múltiples, filtros, permisos, orden y recuperación: OK")
        finally:
            client.drop_database(name)


if __name__ == "__main__":
    main()
