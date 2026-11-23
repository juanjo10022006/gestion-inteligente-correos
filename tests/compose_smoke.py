"""Exercise the built Nginx/API/IA/Mongo stack without displaying test credentials."""
import json
from secrets import token_urlsafe
from urllib.request import Request, urlopen

from backend.db import connect, get_database
from backend.scripts.seed_demo import prepare_demo


def call(path, expected, body=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request("http://web" + path, headers=headers,
                      data=json.dumps(body).encode() if body is not None else None)
    with urlopen(request, timeout=15) as response:
        assert response.status == expected
        raw = response.read()
        return json.loads(raw) if raw else None


def main():
    with urlopen("http://web/", timeout=10) as response:
        assert response.status == 200
        assert b'<div id="root">' in response.read()
    with connect() as client:
        db = get_database(client)
        assert db.name.startswith("compose_smoke_"), "Se requiere una base exclusivamente efímera."
        assert db.users.count_documents({}) == db.messages.count_documents({}) == 0
        prepared = prepare_demo(db, enabled=True, environment="local")
        tokens = {}
        for username, temporary in prepared["newCredentials"].items():
            password = token_urlsafe(24)
            call("/api/v1/auth/activate", 204, {
                "username": username, "temporaryCredential": temporary, "newPassword": password,
            })
            tokens[username] = call("/api/v1/auth/login", 200, {
                "username": username, "password": password,
            })["accessToken"]
        assert prepare_demo(db, enabled=True, environment="local") == {
            "newCredentials": {}, "messagesCreated": 0,
        }
        operator = tokens["demo_operador"]
        message = call("/api/v1/messages", 201, {
            "subject": "Factura de prueba Compose",
            "body": "Necesito una copia de la factura del servicio que ya pagamos.",
        }, operator)
        assert message["prediction"] is not None
        assert call("/api/v1/messages/" + message["id"], 200, token=operator)["id"] == message["id"]
        audit = call("/api/v1/audit-events?messageId=" + message["id"], 200,
                     token=tokens["demo_admin"])
        assert len(audit["items"]) >= 2
        spec = call("/openapi.json", 200)
        assert "/api/v1/users/{username}/activation-credential" in spec["paths"]
    print("Compose efímero: web compilada, proxy, activación/login, demo, IA y auditoría: OK")


if __name__ == "__main__":
    main()
