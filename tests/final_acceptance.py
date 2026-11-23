"""Seed idempotence, OpenAPI and malformed/slow IA integration on a UUID database."""
import json
import os
import pty
import runpy
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4
from unittest.mock import patch

from bson import ObjectId

from backend.db import connect, initialize_database
from backend.scripts.seed_demo import prepare_demo
from backend.users import credential_hash

helpers = runpy.run_path(str(Path(__file__).with_name("compose_acceptance.py")))
access = runpy.run_path(str(Path(__file__).with_name("access_acceptance.py")))


def verify_openapi():
    spec = helpers["call"]("/openapi.json", 200)
    expected = {
        ("post", "/api/v1/auth/login"), ("post", "/api/v1/auth/activate"), ("post", "/api/v1/auth/logout"),
        ("get", "/api/v1/users"), ("post", "/api/v1/users"), ("patch", "/api/v1/users/{username}"),
        ("post", "/api/v1/users/{username}/activation-credential"),
        ("get", "/api/v1/messages"), ("post", "/api/v1/messages"), ("get", "/api/v1/messages/{message_id}"),
        ("patch", "/api/v1/messages/{message_id}/status"),
        ("patch", "/api/v1/messages/{message_id}/classification"), ("get", "/api/v1/audit-events"),
    }
    observed = {(method, path) for path, operations in spec["paths"].items()
                for method in operations if method in {"get", "post", "patch", "delete", "put"}}
    assert observed == expected
    for method, path in expected:
        if path not in {"/api/v1/auth/login", "/api/v1/auth/activate"}:
            assert spec["paths"][path][method]["security"], path
    for path, expected_filters in (
        ("/api/v1/messages", {"text", "status", "department", "dateFrom", "dateTo", "page", "pageSize"}),
        ("/api/v1/audit-events", {"messageId", "actor", "action", "dateFrom", "dateTo", "limit"}),
    ):
        assert expected_filters <= {item["name"] for item in spec["paths"][path]["get"]["parameters"]}


def verify_seed(db):
    for enabled, environment in ((False, "local"), (True, "production")):
        try:
            prepare_demo(db, enabled=enabled, environment=environment)
        except ValueError:
            pass
        else:
            raise AssertionError("Se permitió inicialización demo sin autorización local.")
    assert db.users.count_documents({}) == 0
    first = prepare_demo(db, enabled=True, environment="local")
    assert set(first["newCredentials"]) == {"demo_admin", "demo_operador"}
    assert first["messagesCreated"] == 3
    with helpers["start_api"](db.name, os.environ["AI_SERVICE_URL"]):
        verify_openapi()
        for username, temporary in first["newCredentials"].items():
            password = token_urlsafe(24)
            access["call"]("/auth/activate", 204, body={
                "username": username, "temporaryCredential": temporary, "newPassword": password,
            })
            access["call"]("/auth/login", 200, body={"username": username, "password": password})
    snapshots = {name: list(db[name].find().sort("_id", 1)) for name in ("users", "messages", "audit_events")}
    second = prepare_demo(db, enabled=True, environment="local")
    assert second == {"newCredentials": {}, "messagesCreated": 0}
    for name, previous in snapshots.items():
        assert list(db[name].find().sort("_id", 1)) == previous
    return helpers["create_fixture_user"](db, "operador_fallos", "OPERADOR")


def verify_seed_delivery(client):
    name = "demo_cli_" + uuid4().hex
    db = client[name]
    environment = {**os.environ, "MONGODB_DB_NAME": name, "APP_ENV": "local",
                   "DEMO_SEED_ENABLED": "local-only"}
    # Never inherit a developer's private demo credentials into a test.
    for key in ("DEMO_ADMIN_TEMPORARY_CREDENTIAL", "DEMO_OPERATOR_TEMPORARY_CREDENTIAL"):
        environment.pop(key, None)
    command = [sys.executable, "-m", "backend.scripts.seed_demo", "--confirm-local-demo"]

    def tty_run(env):
        master, slave = pty.openpty()
        try:
            result = subprocess.run(command, env=env, stdin=slave, stdout=slave,
                                    stderr=subprocess.PIPE, timeout=30)
            os.close(slave)
            slave = None
            chunks = []
            while True:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            return result.returncode, b"".join(chunks).decode()
        finally:
            if slave is not None:
                os.close(slave)
            os.close(master)

    try:
        denied = subprocess.run(command, env=environment, capture_output=True, timeout=30)
        assert denied.returncode != 0 and db.users.count_documents({}) == 0
        for invalid in ({**environment, "APP_ENV": "production"},
                        {**environment, "DEMO_SEED_ENABLED": ""}):
            code, _ = tty_run(invalid)
            assert code != 0 and db.users.count_documents({}) == 0
        code, text = tty_run(environment)
        assert code == 0
        rows = [json.loads(line) for line in text.splitlines()]
        assert rows[-1] == {"newAccounts": 2, "messagesCreated": 3}
        for row in rows[:-1]:
            saved = db.users.find_one({"_id": row["username"]})
            assert saved["activated"] is False
            assert saved["activationCredentialHash"] == credential_hash(row["temporaryCredential"])
        code, text = tty_run(environment)
        assert code == 0 and json.loads(text) == {"newAccounts": 0, "messagesCreated": 0}
    finally:
        client.drop_database(name)
    # Credentials are handed off before later message preparation can fail.
    name = "demo_delivery_" + uuid4().hex
    delivered = {}
    try:
        with patch("backend.scripts.seed_demo.persist_message", side_effect=RuntimeError("fallo simulado")):
            try:
                prepare_demo(client[name], enabled=True, environment="local",
                             on_created=lambda username, value: delivered.update({username: value}))
            except RuntimeError:
                pass
            else:
                raise AssertionError("No se inyectó el fallo posterior a la creación de cuentas.")
        assert set(delivered) == {"demo_admin", "demo_operador"}
        assert prepare_demo(client[name], enabled=True, environment="local") == {
            "newCredentials": {}, "messagesCreated": 3,
        }
        for username, temporary in delivered.items():
            assert client[name].users.find_one({"_id": username})["activationCredentialHash"] == credential_hash(temporary)
    finally:
        client.drop_database(name)


def verify_ai_failures(db, credentials):
    observed_before_inference = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            mode = self.server.mode
            saved = db.messages.find_one({"status": "RECIBIDO"}, sort=[("createdAt", -1)])
            identifier = str(saved["_id"]) if saved else None
            observed_before_inference.append((identifier, db.audit_events.count_documents({
                "messageId": identifier, "action": "MENSAJE_REGISTRADO",
            })))
            if mode == "timeout":
                time.sleep(3)
            payload = {
                "json": b'{"incompleto":',
                "category": b'{"category":"OTRO","confidence":0.9,"modelVersion":"x"}',
                "confidence": b'{"category":"VENTAS","confidence":1.5,"modelVersion":"x"}',
                "version": b'{"category":"VENTAS","confidence":0.8,"modelVersion":""}',
                "timeout": b'{}',
            }[mode]
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)
            except OSError:
                pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with helpers["start_api"](db.name, f"http://127.0.0.1:{server.server_port}"):
            token = access["call"]("/auth/login", 200, body=credentials)[1]["accessToken"]
            for mode in ("json", "category", "confidence", "version", "timeout"):
                server.mode = mode
                message = helpers["call"]("/api/v1/messages", 201, token=token, body=helpers["INVOICE"])
                assert observed_before_inference[-1] == (message["id"], 1)
                assert message["status"] == "PENDIENTE_CLASIFICACION"
                assert message["prediction"] is None and message["department"] is None
                saved = db.messages.find_one({"_id": ObjectId(message["id"])})
                assert saved["body"] == helpers["INVOICE"]["body"]
                assert db.audit_events.count_documents({
                    "messageId": message["id"], "action": "CLASIFICACION_NO_DISPONIBLE",
                }) == 1
                helpers["assign"](message["id"], token)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main():
    with connect() as client:
        name = "final_acceptance_" + uuid4().hex
        db = client[name]
        try:
            initialize_database(db)
            verify_seed_delivery(client)
            credentials = verify_seed(db)
            verify_ai_failures(db, credentials)
            print("Demo local idempotente, conservación de cuentas, OpenAPI y fallos IA: OK")
        finally:
            client.drop_database(name)


if __name__ == "__main__":
    main()
