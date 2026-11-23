"""Accounts/session verification on a UUID database in the ephemeral MongoDB runner."""

import json
import os
import runpy
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import token_urlsafe
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

from fastapi import HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials
from pymongo.collection import Collection
from pymongo.errors import AutoReconnect

from backend.access_models import ActivationInput, UserCreate
from backend.audit import publish_pending
from backend.auth import UserIdentity, LoginInput, activate, current_user, login, logout, password_hash, token_digest
from backend.create_user import main as create_cli_user
from backend.db import connect, initialize_database
from backend.users import create_user, renew_activation

helpers = runpy.run_path(str(Path(__file__).with_name("compose_acceptance.py")))


def call(path, expected, token=None, body=None, method=None):
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request("http://127.0.0.1:18000/api/v1" + path, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None, method=method)
    try:
        response = urlopen(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read().decode()
        # Failures must not print response bodies, tokens or one-time credentials.
        if expected is not None:
            assert response.status == expected, (path, expected, response.status)
        payload = json.loads(raw) if raw else None
        return response.status, payload, response.headers


def verify_api(db, admin_credentials, operator_credentials):
    secrets = []
    admin = call("/auth/login", 200, body=admin_credentials)[1]["accessToken"]
    operator = call("/auth/login", 200, body=operator_credentials)[1]["accessToken"]
    secrets.extend([admin, operator, admin_credentials["password"], operator_credentials["password"]])
    account = {"username": "nueva_cuenta", "role": "OPERADOR", "active": True}
    call("/users", 401, body=account)
    call("/users", 403, token=operator, body=account)
    call("/users", 403, token=operator)
    call("/users/admin_cli", 403, token=operator, method="PATCH", body={"role": "OPERADOR", "active": True})
    for invalid in ({**account, "role": "EXTERNO"}, {**account, "username": "invalido/$"},
                    {**account, "active": "false"}, {**account, "password": "never-store-this"}):
        call("/users", 422, token=admin, body=invalid)

    _, created, headers = call("/users", 201, token=admin, body=account)
    assert headers["Cache-Control"] == "no-store"
    temporary = created["temporaryCredential"]
    secrets.append(temporary)
    assert created["user"]["activated"] is False
    assert db.users.find_one({"_id": account["username"]})["activationCredentialHash"] != temporary.encode()
    count = db.audit_events.count_documents({"action": "USUARIO_CREADO"})
    call("/users", 409, token=admin, body=account)
    assert db.audit_events.count_documents({"action": "USUARIO_CREADO"}) == count
    listing = call("/users?pageSize=1&page=1", 200, token=admin)[1]
    assert listing["pageSize"] == 1 and listing["total"] == 3
    all_users = call("/users?pageSize=100", 200, token=admin)[1]["items"]
    allowed = {"id", "username", "role", "active", "activated", "createdAt"}
    assert all(set(item) == allowed for item in all_users)
    assert next(item for item in all_users if item["id"] == "admin_cli")["activated"]
    assert "temporaryCredential" not in json.dumps(all_users)

    call("/users/nueva_cuenta/activation-credential", 401, method="POST")
    call("/users/nueva_cuenta/activation-credential", 403, token=operator, method="POST")
    old_temporary = temporary
    _, renewed, _ = call("/users/nueva_cuenta/activation-credential", 200, token=admin, method="POST")
    temporary = renewed["temporaryCredential"]
    assert temporary != old_temporary
    secrets.append(temporary)
    call("/auth/activate", 401, body={"username": account["username"], "temporaryCredential": old_temporary,
                                     "newPassword": "contraseña de prueba suficientemente larga"})

    new_password = "una frase suficientemente larga"
    secrets.append(new_password)
    activation = {"username": account["username"], "temporaryCredential": temporary, "newPassword": new_password}
    call("/auth/login", 401, body={"username": account["username"], "password": new_password})
    call("/auth/activate", 401, body={**activation, "temporaryCredential": "incorrecta"})
    for bad in ("corta", " " * 12, "x" * 257):
        _, error, _ = call("/auth/activate", 422, body={**activation, "newPassword": bad})
        assert bad not in json.dumps(error)
        assert "temporaryCredential" not in json.dumps(error)
    db.users.update_one({"_id": account["username"]},
                        {"$set": {"activationExpiresAt": datetime.now(timezone.utc) - timedelta(seconds=1)}})
    call("/auth/activate", 401, body=activation)
    _, replacement, headers = call("/users/nueva_cuenta/activation-credential", 200,
                                    token=admin, method="POST")
    assert headers["Cache-Control"] == "no-store"
    call("/auth/activate", 401, body=activation)
    temporary = replacement["temporaryCredential"]
    secrets.append(temporary)
    activation["temporaryCredential"] = temporary
    # The same one-time credential cannot succeed twice, even concurrently.
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: call("/auth/activate", None, body=activation)[0], range(2)))
    assert sorted(results) == [204, 401]
    call("/auth/activate", 401, body=activation)
    saved = db.users.find_one({"_id": account["username"]})
    call("/users/nueva_cuenta/activation-credential", 409, token=admin, method="POST")
    assert "activationCredentialHash" not in saved and "activationExpiresAt" not in saved
    assert saved["passwordHash"] != new_password.encode()

    credentials = {"username": account["username"], "password": new_password}
    first = call("/auth/login", 200, body=credentials)[1]["accessToken"]
    second = call("/auth/login", 200, body=credentials)[1]["accessToken"]
    secrets.extend([first, second])
    call("/auth/logout", 204, token=first, method="POST")
    call("/messages", 401, token=first)
    call("/auth/logout", 401, token=first, method="POST")
    call("/messages", 200, token=second)
    call("/auth/logout", 401, method="POST")

    # Disabling, re-enabling and changing role never resurrect old sessions.
    call("/users/nueva_cuenta", 200, token=admin, method="PATCH", body={"role": "OPERADOR", "active": False})
    call("/messages", 401, token=second)
    call("/auth/login", 401, body=credentials)
    call("/users/nueva_cuenta", 200, token=admin, method="PATCH", body={"role": "OPERADOR", "active": True})
    call("/messages", 401, token=second)
    third = call("/auth/login", 200, body=credentials)[1]["accessToken"]
    secrets.append(third)
    call("/users/nueva_cuenta", 200, token=admin, method="PATCH", body={"role": "ADMINISTRADOR", "active": True})
    call("/users", 401, token=third)
    elevated = call("/auth/login", 200, body=credentials)[1]["accessToken"]
    secrets.append(elevated)
    call("/users", 200, token=elevated)
    call("/users/nueva_cuenta", 200, token=admin, method="PATCH", body={"role": "OPERADOR", "active": True})
    call("/users", 401, token=elevated)
    call("/users/admin_cli", 409, token=admin, method="PATCH", body={"role": "OPERADOR", "active": True})
    call("/users/no_existe", 404, token=admin, method="PATCH", body={"role": "OPERADOR", "active": True})
    call("/users/nueva_cuenta", 422, token=admin, method="PATCH", body={"role": "EXTERNO", "active": True})

    fourth = call("/auth/login", 200, body=credentials)[1]["accessToken"]
    secrets.append(fourth)
    # TTL is only cleanup; authorization checks expiry immediately.
    db.sessions.update_one({"_id": token_digest(fourth)},
                           {"$set": {"validUntil": datetime.now(timezone.utc) - timedelta(seconds=1)}})
    call("/messages", 401, token=fourth)
    # A real pre-existing session without authVersion/validUntil remains compatible.
    legacy_token = "legacy-test-session-" + uuid4().hex
    secrets.append(legacy_token)
    db.sessions.insert_one({"_id": token_digest(legacy_token), "userId": "operador_cli",
                            "createdAt": datetime.now(timezone.utc),
                            "expiresAt": datetime.now(timezone.utc) + timedelta(hours=1)})
    call("/messages", 200, token=legacy_token)
    call("/auth/logout", 204, token=legacy_token, method="POST")
    call("/messages", 401, token=legacy_token)

    # Disabled accounts can be created but cannot activate until an admin enables them.
    _, disabled, _ = call("/users", 201, token=admin,
                         body={"username": "admin_pendiente", "role": "ADMINISTRADOR", "active": False})
    secrets.append(disabled["temporaryCredential"])
    disabled_activation = {"username": "admin_pendiente", "temporaryCredential": disabled["temporaryCredential"],
                           "newPassword": new_password}
    call("/auth/activate", 401, body=disabled_activation)
    call("/users/admin_pendiente", 200, token=admin, method="PATCH",
         body={"role": "ADMINISTRADOR", "active": True})
    call("/auth/activate", 204, body=disabled_activation)
    # Account/session events have no message ID and remain queryable in global audit.
    _, audit, _ = call("/audit-events?limit=100", 200, token=admin)
    actions = {item["action"] for item in audit["items"]}
    assert {"USUARIO_CREADO", "CUENTA_ACTIVADA", "USUARIO_ACTUALIZADO",
            "SESION_INICIADA", "SESION_CERRADA"} <= actions
    assert all(item["messageId"] is None for item in audit["items"])
    _, selected, _ = call("/audit-events?actor=admin_cli&action=USUARIO_CREADO", 200, token=admin)
    assert len(selected["items"]) == 2
    for data in (audit, all_users, list(db.audit_events.find()), saved):
        encoded = json.dumps(data, default=str)
        assert all(value not in encoded for value in secrets), "Se encontró un secreto en persistencia/respuesta."
    serialized_audit = json.dumps(audit)
    for forbidden in ("passwordHash", "activationCredentialHash", "accessToken", "temporaryCredential", "salt"):
        assert forbidden not in serialized_audit
    # Initial CLI documents were not deleted or changed by any migration.
    assert db.users.find_one({"_id": "admin_cli"})["passwordHash"]
    return actions


def verify_outbox(db, legacy_credentials):
    """Publication failures do not lose account/session events or resurrect tokens."""
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db)))
    original = Collection.insert_one
    def fail_events(collection, document, *args, **kwargs):
        if collection.name == "audit_events":
            raise AutoReconnect("fallo simulado de publicación")
        return original(collection, document, *args, **kwargs)
    with patch.object(Collection, "insert_one", fail_events):
        response = Response()
        created = create_user(UserCreate(username="cuenta_recuperacion", role="OPERADOR"), request, response,
                              UserIdentity(id="admin_cli", role="ADMINISTRADOR"))
        assert created.temporaryCredential and response.headers["X-Audit-Status"] == "pending"
    assert db.users.find_one({"_id": "cuenta_recuperacion"})["pendingAudit"]
    publish_pending(db)
    assert not db.users.find_one({"_id": "cuenta_recuperacion"})["pendingAudit"]
    with patch.object(Collection, "insert_one", fail_events):
        response = Response()
        result = login(LoginInput(**legacy_credentials), request, response)
        assert result.accessToken and response.headers["X-Audit-Status"] == "pending"
    pending = db.sessions.find_one({"pendingAudit.0": {"$exists": True}})
    assert pending and "expiresAt" not in pending  # TTL cannot erase unpublished events.
    publish_pending(db)
    recovered = db.sessions.find_one({"_id": pending["_id"]})
    assert recovered["expiresAt"] == recovered["validUntil"]
    count = db.audit_events.count_documents({})
    publish_pending(db)
    assert db.audit_events.count_documents({}) == count
    with patch.object(Collection, "insert_one", fail_events):
        response = Response()
        renewed = renew_activation("cuenta_recuperacion", request, response, UserIdentity(id="admin_cli", role="ADMINISTRADOR"))
        assert response.headers["X-Audit-Status"] == "pending"
        activation = ActivationInput(username="cuenta_recuperacion",
                                     temporaryCredential=renewed.temporaryCredential,
                                     newPassword="contraseña segura para recuperación")
        activation_response = activate(activation, request)
        assert activation_response.status_code == 204
        assert activation_response.headers["X-Audit-Status"] == "pending"
    publish_pending(db)
    assert db.users.find_one({"_id": "cuenta_recuperacion"})["activated"]
    assert db.audit_events.count_documents({"action": "CUENTA_ACTIVADA",
                                           "actorUserId": "cuenta_recuperacion"}) == 1
    assert db.users.count_documents({"pendingAudit.0": {"$exists": True}}) == 0
    # The activated account is usable even though publication previously failed.
    response = Response()
    credentials = LoginInput(username="cuenta_recuperacion", password="contraseña segura para recuperación")
    logged_in = login(credentials, request, response)
    bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials=logged_in.accessToken)
    identity = current_user(request, bearer)
    with patch.object(Collection, "insert_one", fail_events):
        response = logout(request, identity, bearer)
        assert response.status_code == 204 and response.headers["X-Audit-Status"] == "pending"
    try:
        current_user(request, bearer)
    except HTTPException as error:
        assert error.status_code == 401
    else:
        raise AssertionError("Logout pendiente de auditoría no revocó la sesión.")
    publish_pending(db)
    count = db.audit_events.count_documents({})
    publish_pending(db)
    assert db.audit_events.count_documents({}) == count
    encoded = json.dumps(list(db.audit_events.find()) + list(db.users.find()), default=str)
    for secret in (created.temporaryCredential, renewed.temporaryCredential, logged_in.accessToken,
                   credentials.password.get_secret_value()):
        assert secret not in encoded


def verify_renewal_race(db):
    """A renewal invalidates an activation that already started hashing the old secret."""
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(db=db)))
    admin = UserIdentity(id="admin_cli", role="ADMINISTRADOR")
    created = create_user(UserCreate(username="activacion_concurrente", role="OPERADOR"),
                          request, Response(), admin)
    started, release = Event(), Event()

    def paused_hash(*args, **kwargs):
        started.set()
        assert release.wait(10), "No se liberó la activación concurrente."
        return password_hash(*args, **kwargs)

    payload = ActivationInput(username="activacion_concurrente",
                              temporaryCredential=created.temporaryCredential,
                              newPassword=token_urlsafe(24))
    with ThreadPoolExecutor(max_workers=1) as executor:
        with patch("backend.auth.password_hash", side_effect=paused_hash):
            future = executor.submit(activate, payload, request)
            try:
                assert started.wait(10), "La activación no alcanzó el punto de concurrencia."
                renewed = renew_activation(payload.username, request, Response(), admin)
            finally:
                release.set()
            try:
                future.result(timeout=15)
            except HTTPException as error:
                assert error.status_code == 401
            else:
                raise AssertionError("Se consumió una credencial invalidada por renovación.")
    payload = ActivationInput(username=payload.username, temporaryCredential=renewed.temporaryCredential,
                              newPassword=payload.newPassword)
    assert activate(payload, request).status_code == 204
    assert db.audit_events.count_documents({"action": "CUENTA_ACTIVADA",
                                           "actorUserId": payload.username}) == 1


def verify_cli(db):
    password = token_urlsafe(24)
    with patch("sys.argv", ["create_user", "bootstrap_prueba", "ADMINISTRADOR"]), \
            patch("backend.create_user.get_database", return_value=db), \
            patch("backend.create_user.getpass", side_effect=[password] * 2):
        create_cli_user()
    assert db.users.find_one({"_id": "bootstrap_prueba"})["passwordHash"]
    event = db.audit_events.find_one({"after.username": "bootstrap_prueba"})
    assert event["actorType"] == "SISTEMA" and event["action"] == "USUARIO_CREADO"
    assert "passwordHash" not in json.dumps(event, default=str)
    return {"username": "bootstrap_prueba", "password": password}


def main():
    with connect() as client:
        name = "access_acceptance_" + uuid4().hex
        db = client[name]
        try:
            initialize_database(db)
            admin = helpers["create_fixture_user"](db, "admin_cli", "ADMINISTRADOR")
            operator = helpers["create_fixture_user"](db, "operador_cli", "OPERADOR")
            with helpers["start_api"](name, os.environ["AI_SERVICE_URL"]):
                verify_api(db, admin, operator)
                cli_credentials = verify_cli(db)
                call("/auth/login", 200, body=cli_credentials)
            verify_outbox(db, operator)
            verify_renewal_race(db)
            print("Usuarios, activación, revocación, compatibilidad CLI, permisos y auditoría sin secretos: OK")
        finally:
            client.drop_database(name)


if __name__ == "__main__":
    main()
