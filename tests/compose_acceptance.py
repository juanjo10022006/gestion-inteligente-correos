"""Run inside the API container against a disposable database."""

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from secrets import token_bytes, token_urlsafe
from statistics import median, quantiles
from time import perf_counter, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from backend.auth import password_hash
from backend.db import connect

BASE = "http://127.0.0.1:18000"
MESSAGES = "/api/v1/messages"
AUDIT = "/api/v1/audit-events"
LOGIN = "/api/v1/auth/login"
INVOICE = {
    "subject": "Solicitud de factura",
    "body": "Hola, necesito una copia de la factura del servicio que ya pagamos.",
}
AMBIGUOUS = {"subject": "Consulta", "body": "Buen día, agradezco su orientación con esto."}


def call(path, expected, *, token=None, body=None, method=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    data = json.dumps(body).encode() if body is not None else None
    request = Request(BASE + path, headers=headers, data=data, method=method)
    try:
        response = urlopen(request, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        payload = json.load(response)
        assert response.status == expected, (path, expected, response.status, payload)
    return payload


@contextmanager
def start_api(database, ai_url):
    environment = {
        **os.environ,
        "MONGODB_DB_NAME": database,
        "AI_SERVICE_URL": ai_url,
        "ROUTING_THRESHOLD": "0.45",
    }
    process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "127.0.0.1", "--port", "18000", "--no-access-log",
    ], env=environment)
    try:
        for _ in range(40):
            if process.poll() is not None:
                raise RuntimeError("La API de prueba terminó antes de arrancar.")
            try:
                call("/openapi.json", 200)
                break
            except URLError:
                sleep(0.25)
        else:
            raise RuntimeError("La API de prueba no respondió.")
        yield
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)


def create_fixture_user(db, username, role):
    password = token_urlsafe(18)
    salt = token_bytes(16)
    db.users.insert_one({
        "_id": username,
        "role": role,
        "active": True,
        "salt": salt,
        "passwordHash": password_hash(password, salt),
    })
    return {"username": username, "password": password}


def assign(message_id, token):
    return call(f"{MESSAGES}/{message_id}/classification", 200, token=token, method="PATCH",
                body={"department": "FACTURACION", "reason": "Asignación ficticia para la prueba."})


def run_cases(db, operator_login, admin_login):
    call(MESSAGES, 401)
    call(LOGIN, 401, body={**operator_login, "password": token_urlsafe(18)})
    operator = call(LOGIN, 200, body=operator_login)["accessToken"]
    administrator = call(LOGIN, 200, body=admin_login)["accessToken"]
    call(AUDIT, 403, token=operator)
    call(MESSAGES, 422, token=operator, body={"subject": "ab", "body": "Mensaje ficticio inválido."})
    assert db.messages.count_documents({}) == 0
    print("CP-02 y CP-08 (inicio de sesión y permisos): OK")

    invoice = call(MESSAGES, 201, token=operator, body=INVOICE)
    assert invoice["status"] == "CLASIFICADO" and invoice["department"] == "FACTURACION"
    assert 0.45 <= invoice["prediction"]["confidence"] <= 1
    assert invoice["prediction"]["modelVersion"]
    saved = call(f"{MESSAGES}/{invoice['id']}", 200, token=operator)
    assert saved["prediction"] == invoice["prediction"] and saved["body"] == INVOICE["body"]
    review = call(MESSAGES, 201, token=operator, body=AMBIGUOUS)
    assert review["status"] == "PENDIENTE_REVISION" and review["department"] is None
    assert 0 <= review["prediction"]["confidence"] < 0.45
    print("CP-01 (creación), CP-03 y CP-04: OK")

    invoice_status = f"{MESSAGES}/{invoice['id']}/status"
    review_status = f"{MESSAGES}/{review['id']}/status"
    closure = {"status": "CERRADO", "reason": "Se envió la factura solicitada."}
    call(invoice_status, 409, token=operator, method="PATCH", body=closure)
    call(review_status, 409, token=operator, method="PATCH", body=closure)
    listing = call(f"{MESSAGES}?text=factura&pageSize=1&page=1", 200, token=operator)
    assert listing["total"] == 1 and listing["items"][0]["id"] == invoice["id"]
    assert not call(f"{MESSAGES}?pageSize=1&page=3", 200, token=operator)["items"]
    call(f"{MESSAGES}/000000000000000000000000", 404, token=operator)
    assigned = assign(review["id"], operator)
    assert assigned["status"] == "EN_GESTION" and assigned["prediction"] == review["prediction"]
    call(f"{MESSAGES}/{review['id']}/classification", 409, token=operator, method="PATCH",
         body={"department": "FACTURACION", "reason": "Intento de reasignación ficticia."})
    assert call(f"{MESSAGES}/{review['id']}", 200, token=operator) == assigned
    events = call(f"{AUDIT}?messageId={review['id']}", 200, token=administrator)["items"]
    by_action = {event["action"]: event for event in events}
    assert set(by_action) == {"MENSAJE_REGISTRADO", "CLASIFICACION_EN_REVISION", "CLASIFICACION_MANUAL"}
    assert by_action["MENSAJE_REGISTRADO"]["actorUserId"] == operator_login["username"]
    assert by_action["CLASIFICACION_EN_REVISION"]["actorUserId"] == "SISTEMA"
    assert by_action["CLASIFICACION_MANUAL"]["reason"] == "Asignación ficticia para la prueba."
    managed = call(invoice_status, 200, token=operator, method="PATCH", body={"status": "EN_GESTION"})
    assert managed["status"] == "EN_GESTION" and managed["prediction"] == invoice["prediction"]
    call(invoice_status, 422, token=operator, method="PATCH", body={"status": "CERRADO"})
    call(invoice_status, 422, token=operator, method="PATCH", body={"status": "CERRADO", "reason": "   "})
    closed = call(invoice_status, 200, token=operator, method="PATCH", body=closure)
    assert closed["status"] == "CERRADO" and closed["resolution"] == closure["reason"]
    assert closed["prediction"] == invoice["prediction"]
    call(invoice_status, 409, token=operator, method="PATCH", body=closure)
    events = call(f"{AUDIT}?messageId={invoice['id']}", 200, token=administrator)["items"]
    closure_events = [event for event in events if event["action"] == "MENSAJE_CERRADO"]
    assert len(closure_events) == 1
    assert closure_events[0]["reason"] == closure["reason"]
    assert closure_events[0]["actorUserId"] == operator_login["username"]
    assert any(event["action"] == "GESTION_INICIADA" for event in events)
    assert call(f"{MESSAGES}/{invoice['id']}", 200, token=operator) == closed
    print("CP-05, CP-06 (asignación, gestión, cierre y conflictos) y CP-07: OK")
    return operator


def measure(token):
    for path, expected, body, target in (
        (MESSAGES, 201, INVOICE, 5000),
        (MESSAGES, 200, None, 2000),
    ):
        samples = []
        for _ in range(30):
            start = perf_counter()
            call(path, expected, token=token, body=body)
            samples.append((perf_counter() - start) * 1000)
        p95 = quantiles(samples, n=100, method="inclusive")[94]
        assert p95 <= target, (path, p95, target)
        method = "POST" if body else "GET"
        print(f"{method} {path}: n={len(samples)}, mediana={median(samples):.2f} ms, p95={p95:.2f} ms")


def main():
    with connect() as mongo:
        database = mongo["compose_acceptance_" + uuid4().hex]
        try:
            operator_login = create_fixture_user(database, "operador_prueba", "OPERADOR")
            admin_login = create_fixture_user(database, "admin_prueba", "ADMINISTRADOR")
            with start_api(database.name, os.environ["AI_SERVICE_URL"]):
                token = run_cases(database, operator_login, admin_login)
                measure(token)
            with start_api(database.name, "http://127.0.0.1:1"):
                failure = call(MESSAGES, 201, token=token, body=INVOICE)
                assert failure["status"] == "PENDIENTE_CLASIFICACION" and failure["prediction"] is None
                assert call(f"{MESSAGES}/{failure['id']}", 200, token=token)["body"] == INVOICE["body"]
                result = assign(failure["id"], token)
                assert result["status"] == "EN_GESTION" and result["prediction"] is None
                print("CP-10 (IA no disponible y asignación manual): OK")
        finally:
            mongo.drop_database(database.name)


if __name__ == "__main__":
    main()
