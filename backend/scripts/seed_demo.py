"""Explicit local-only demo bootstrap; never run automatically at API startup."""
import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from backend.audit import make_event, publish_after_commit
from backend.db import connect, get_database, initialize_database
from backend.main import persist_message
from backend.schemas import MessageInput
from backend.users import credential_hash, temporary_duration, user_view


def prepare_demo(db, *, enabled=False, environment=None, credentials=None, threshold=0.45, on_created=None):
    if not enabled or environment != "local":
        raise ValueError("La preparación demo requiere habilitación explícita y APP_ENV=local.")
    initialize_database(db)
    delivered = {}
    for username, role in (("demo_admin", "ADMINISTRADOR"), ("demo_operador", "OPERADOR")):
        if db.users.find_one({"_id": username}, {"_id": 1}) is not None:
            continue
        temporary = (credentials or {}).get(username) or secrets.token_urlsafe(32)
        if len(temporary) < 32:
            raise ValueError("Una credencial demo privada debe tener al menos 32 caracteres.")
        now = datetime.now(timezone.utc)
        document = {
            "_id": username, "role": role, "active": True, "activated": False,
            "activationCredentialHash": credential_hash(temporary),
            "activationExpiresAt": now + temporary_duration, "createdAt": now, "updatedAt": now,
            "revision": 0, "authVersion": 0,
        }
        document["pendingAudit"] = [make_event(None, "USUARIO_CREADO", None, None, user_view(document))]
        try:
            db.users.insert_one(document)
        except DuplicateKeyError:
            continue
        publish_after_commit(db, "users", username)
        delivered[username] = temporary
        if on_created is not None:
            on_created(username, temporary)
    messages_created = 0
    for number, (subject, body) in enumerate((
        ("Copia de factura demo", "Necesito una copia de la factura del servicio que ya pagamos."),
        ("Acceso al portal demo", "El portal muestra un error de conexión y no permite iniciar sesión."),
        ("Consulta demo", "Buen día, agradezco su orientación con esta solicitud de prueba."),
    )):
        identifier = ObjectId(hashlib.sha256(f"demo-v1-message-{number}".encode()).hexdigest()[:24])
        if db.messages.find_one({"_id": identifier}, {"_id": 1}) is not None:
            continue
        try:
            persist_message(MessageInput(subject=subject, body=body), db, "demo_operador", threshold, identifier)
            messages_created += 1
        except DuplicateKeyError:
            continue
    return {"newCredentials": delivered, "messagesCreated": messages_created}


def main():
    parser = argparse.ArgumentParser(description="Preparar cuentas ficticias pendientes y mensajes demo en local.")
    parser.add_argument("--confirm-local-demo", action="store_true")
    args = parser.parse_args()
    if not sys.stdout.isatty():
        parser.error("Usa una terminal interactiva local; no se entregan credenciales en logs o archivos.")
    enabled = args.confirm_local_demo and os.environ.get("DEMO_SEED_ENABLED") == "local-only"
    private = {name: os.environ.get(key) for name, key in (
        ("demo_admin", "DEMO_ADMIN_TEMPORARY_CREDENTIAL"), ("demo_operador", "DEMO_OPERATOR_TEMPORARY_CREDENTIAL"),
    )}
    with connect() as client:
        result = prepare_demo(get_database(client), enabled=enabled, environment=os.environ.get("APP_ENV"),
                              credentials=private, threshold=float(os.environ.get("ROUTING_THRESHOLD", "0.45")),
                              on_created=lambda username, value: print(
                                  json.dumps({"username": username, "temporaryCredential": value}), flush=True))
    print(json.dumps({"newAccounts": len(result["newCredentials"]), "messagesCreated": result["messagesCreated"]}))


if __name__ == "__main__":
    main()
