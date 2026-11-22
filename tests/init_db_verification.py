"""Verify idempotent MongoDB initialization against an isolated test database."""

import os
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pymongo.errors import WriteError

from backend.db import (
    COLLECTION_VALIDATORS,
    VALIDATION_ACTION,
    VALIDATION_LEVEL,
    connect,
    get_database,
    initialize_database,
)


def index_snapshot(database):
    return {
        name: {
            index["name"]: {
                "key": list(index["key"].items()),
                "expireAfterSeconds": index.get("expireAfterSeconds"),
                "sparse": index.get("sparse", False),
                "unique": index.get("unique", False),
            }
            for index in database[name].list_indexes()
        }
        for name in COLLECTION_VALIDATORS
    }


def collection_counts(database):
    return {
        name: database[name].count_documents({})
        for name in COLLECTION_VALIDATORS
        if name in database.list_collection_names()
    }


def seed_legacy_documents(database):
    now = datetime.now(timezone.utc)
    database.users.insert_one({
        "_id": "operador_existente",
        "role": "OPERADOR",
        "active": True,
        "salt": b"0123456789abcdef",
        "passwordHash": b"x" * 64,
    })
    database.sessions.insert_one({
        "_id": "a" * 64,
        "userId": "operador_existente",
        "createdAt": now,
        "expiresAt": now + timedelta(hours=1),
    })
    database.messages.insert_one({
        "_id": ObjectId(),
        "subject": "Mensaje existente",
        "body": "Contenido ficticio anterior a la inicialización.",
        "sender": None,
        "status": "PENDIENTE_CLASIFICACION",
        "department": None,
        "prediction": None,
        "createdAt": now,
        "createdBy": "operador_existente",
        "creationEvent": {
            "action": "MENSAJE_REGISTRADO",
            "messageId": "0" * 24,
            "actorUserId": "operador_existente",
            "createdAt": now,
        },
    })
    database.messages.create_index("subject", name="legacy_subject_1")


def assert_validation_options(database):
    info = {entry["name"]: entry["options"] for entry in database.list_collections()}
    for name, validator in COLLECTION_VALIDATORS.items():
        options = info[name]
        assert options["validator"] == validator
        assert options["validationLevel"] == VALIDATION_LEVEL
        assert options["validationAction"] == VALIDATION_ACTION


def verify_post_validation_writes(database):
    now = datetime.now(timezone.utc)
    database.messages.insert_one({
        "_id": ObjectId(),
        "subject": "Mensaje compatible",
        "body": "Contenido ficticio posterior a la inicialización.",
        "status": "RECIBIDO",
        "createdAt": now,
        "createdBy": "operador_existente",
    })
    database.audit_events.insert_one({
        "_id": ObjectId(),
        "messageId": "1" * 24,
        "actorType": "SISTEMA",
        "action": "EVENTO_DE_PRUEBA",
        "createdAt": now,
    })
    database.model_metadata.insert_one({
        "_id": ObjectId(),
        "modelVersion": "modelo-prueba",
        "algorithm": "TF-IDF + regresión logística",
        "datasetVersion": "sintetico-prueba",
        "createdAt": now,
    })

    before = database.messages.count_documents({})
    try:
        database.messages.insert_one({
            "_id": ObjectId(),
            "subject": "Inválido",
            "body": "Este documento usa un estado inválido.",
            "status": "ESTADO_INEXISTENTE",
            "createdAt": now,
            "createdBy": "operador_existente",
        })
    except WriteError:
        pass
    else:
        raise AssertionError("El validador de mensajes aceptó un estado inexistente.")
    assert database.messages.count_documents({}) == before


def main():
    database_name = os.environ.get("MONGODB_DB_NAME", "")
    if not database_name.startswith("init_db_test_"):
        raise RuntimeError("MONGODB_DB_NAME debe comenzar por init_db_test_.")

    with connect() as client:
        database = get_database(client)
        assert not database.list_collection_names(), "La base temporal debe iniciar vacía."
        seed_legacy_documents(database)
        counts_before = collection_counts(database)

        first = initialize_database(database)
        counts_after_first = collection_counts(database)
        indexes_after_first = index_snapshot(database)
        assert counts_after_first["users"] == counts_before["users"]
        assert counts_after_first["sessions"] == counts_before["sessions"]
        assert counts_after_first["messages"] == counts_before["messages"]
        assert "legacy_subject_1" in indexes_after_first["messages"]

        second = initialize_database(database)
        assert index_snapshot(database) == indexes_after_first
        assert collection_counts(database) == counts_after_first
        assert first == second
        assert_validation_options(database)
        verify_post_validation_writes(database)

        assert database.sessions.index_information()["expiresAt_1"]["expireAfterSeconds"] == 0
        print("Inicialización MongoDB idempotente y compatible: OK")


if __name__ == "__main__":
    main()
