import os

from pymongo import ASCENDING, DESCENDING, MongoClient


VALIDATION_LEVEL = "moderate"
VALIDATION_ACTION = "error"

COLLECTION_VALIDATORS = {
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "role", "active"],
            "properties": {
                "_id": {
                    "bsonType": "string",
                    "minLength": 1,
                    "maxLength": 64,
                    "pattern": r"^[A-Za-z0-9._-]+$",
                },
                "role": {"enum": ["OPERADOR", "ADMINISTRADOR"]},
                "active": {"bsonType": "bool"},
                "salt": {"bsonType": "binData"},
                "passwordHash": {"bsonType": "binData"},
                "activationCredentialHash": {"bsonType": "binData"},
                "createdAt": {"bsonType": "date"},
                "updatedAt": {"bsonType": "date"},
            },
        }
    },
    "sessions": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "userId", "createdAt", "expiresAt"],
            "properties": {
                "_id": {"bsonType": "string", "pattern": r"^[a-f0-9]{64}$"},
                "userId": {"bsonType": "string", "minLength": 1, "maxLength": 64},
                "createdAt": {"bsonType": "date"},
                "expiresAt": {"bsonType": "date"},
            },
        }
    },
    "messages": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "subject", "body", "status", "createdAt", "createdBy"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "subject": {"bsonType": "string", "minLength": 3, "maxLength": 160},
                "body": {"bsonType": "string", "minLength": 10, "maxLength": 10_000},
                "sender": {"bsonType": ["string", "null"]},
                "status": {
                    "enum": [
                        "RECIBIDO",
                        "PENDIENTE_CLASIFICACION",
                        "PENDIENTE_REVISION",
                        "CLASIFICADO",
                        "EN_GESTION",
                        "CERRADO",
                    ]
                },
                "department": {
                    "enum": [
                        None,
                        "SOPORTE_TECNICO",
                        "VENTAS",
                        "RECURSOS_HUMANOS",
                        "FACTURACION",
                    ]
                },
                "createdAt": {"bsonType": "date"},
                "createdBy": {"bsonType": "string", "minLength": 1, "maxLength": 64},
                "resolution": {"bsonType": ["string", "null"]},
                "prediction": {
                    "bsonType": ["object", "null"],
                    "properties": {
                        "category": {
                            "enum": [
                                "SOPORTE_TECNICO",
                                "VENTAS",
                                "RECURSOS_HUMANOS",
                                "FACTURACION",
                            ]
                        },
                        "confidence": {
                            "bsonType": ["double", "decimal", "int", "long"],
                            "minimum": 0,
                            "maximum": 1,
                        },
                        "modelVersion": {"bsonType": "string", "minLength": 1, "maxLength": 128},
                        "preprocessingVersion": {"bsonType": "string", "minLength": 1, "maxLength": 128},
                        "source": {"enum": ["IA"]},
                        "timestamp": {"bsonType": "date"},
                    },
                },
            },
        }
    },
    "audit_events": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "actorType", "action", "createdAt"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "messageId": {
                    "bsonType": ["objectId", "string", "null"],
                },
                "actorType": {"enum": ["SISTEMA", "USUARIO"]},
                "actorUserId": {"bsonType": ["string", "null"]},
                "action": {"bsonType": "string", "minLength": 1, "maxLength": 128},
                "reason": {"bsonType": ["string", "null"]},
                "createdAt": {"bsonType": "date"},
            },
        }
    },
    "model_metadata": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "modelVersion"],
            "properties": {
                "_id": {"bsonType": "objectId"},
                "modelVersion": {"bsonType": "string", "minLength": 1, "maxLength": 128},
                "algorithm": {"bsonType": "string"},
                "datasetVersion": {"bsonType": "string"},
                "createdAt": {"bsonType": "date"},
            },
        }
    },
}

INDEXES = {
    "sessions": [
        ([("expiresAt", ASCENDING)], "expiresAt_1", {"expireAfterSeconds": 0}),
    ],
    "messages": [
        ([("createdAt", DESCENDING), ("_id", DESCENDING)], "messages_created_desc", {}),
        (
            [("status", ASCENDING), ("createdAt", DESCENDING), ("_id", DESCENDING)],
            "messages_status_created_desc",
            {},
        ),
        (
            [("department", ASCENDING), ("createdAt", DESCENDING), ("_id", DESCENDING)],
            "messages_department_created_desc",
            {},
        ),
    ],
    "audit_events": [
        ([("createdAt", DESCENDING), ("_id", DESCENDING)], "audit_created_desc", {}),
        (
            [("messageId", ASCENDING), ("createdAt", DESCENDING), ("_id", DESCENDING)],
            "audit_message_created_desc",
            {"sparse": True},
        ),
        (
            [("actorUserId", ASCENDING), ("createdAt", DESCENDING), ("_id", DESCENDING)],
            "audit_actor_created_desc",
            {"sparse": True},
        ),
        (
            [("action", ASCENDING), ("createdAt", DESCENDING), ("_id", DESCENDING)],
            "audit_action_created_desc",
            {},
        ),
    ],
    "model_metadata": [
        ([("modelVersion", ASCENDING)], "model_version_unique", {"unique": True}),
    ],
}


def connect():
    uri = os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017")
    return MongoClient(uri, serverSelectionTimeoutMS=2000, tz_aware=True)


def get_database(client):
    return client[os.environ.get("MONGODB_DB_NAME", "gestion_correos")]


def _ensure_collection(database, name, validator):
    options = {
        "validator": validator,
        "validationLevel": VALIDATION_LEVEL,
        "validationAction": VALIDATION_ACTION,
    }
    if name in database.list_collection_names():
        database.command("collMod", name, **options)
    else:
        database.create_collection(name, **options)


def _ensure_index(collection, keys, name, options):
    expected_keys = list(keys)
    for existing in collection.list_indexes():
        existing_keys = list(existing["key"].items())
        if existing["name"] != name and existing_keys != expected_keys:
            continue
        if existing_keys != expected_keys:
            raise RuntimeError(
                f"El índice {collection.name}.{name} ya existe con otras claves; no se reemplazó."
            )
        for option, expected in options.items():
            actual = existing.get(option, False if option in {"sparse", "unique"} else None)
            if actual != expected:
                raise RuntimeError(
                    f"El índice {collection.name}.{existing['name']} tiene {option}={actual!r}; "
                    f"se esperaba {expected!r}. No se reemplazó."
                )
        return existing["name"]
    return collection.create_index(keys, name=name, **options)


def initialize_database(database):
    """Create or update validators and indexes without changing application documents."""
    for name, validator in COLLECTION_VALIDATORS.items():
        _ensure_collection(database, name, validator)

    configured_indexes = {}
    for collection_name, specifications in INDEXES.items():
        collection = database[collection_name]
        configured_indexes[collection_name] = [
            _ensure_index(collection, keys, name, options)
            for keys, name, options in specifications
        ]

    return {
        "database": database.name,
        "collections": sorted(COLLECTION_VALIDATORS),
        "indexes": configured_indexes,
        "validationLevel": VALIDATION_LEVEL,
        "validationAction": VALIDATION_ACTION,
    }
