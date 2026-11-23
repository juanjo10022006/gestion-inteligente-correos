from argparse import ArgumentParser
from getpass import getpass
from secrets import token_bytes

from pymongo.errors import DuplicateKeyError

from backend.auth import password_hash
from backend.access_models import validate_password
from backend.db import connect, get_database
from backend.audit import make_event, publish_collection_pending
from backend.users import user_view


def main():
    parser = ArgumentParser(description="Crear una cuenta de prueba activa para el entorno local.")
    parser.add_argument("username")
    parser.add_argument("role", choices=("OPERADOR", "ADMINISTRADOR"))
    args = parser.parse_args()
    if not 1 <= len(args.username) <= 64 or not all(c.isalnum() or c in "._-" for c in args.username):
        parser.error("El usuario debe contener entre 1 y 64 letras, números o caracteres ._-")
    password = getpass("Contraseña nueva: ")
    try:
        validate_password(password)
    except ValueError as error:
        parser.error(str(error))
    if password != getpass("Repite la contraseña: "):
        parser.error("Las contraseñas no coinciden.")
    salt = token_bytes(16)
    with connect() as client:
        database = get_database(client)
        document = {
            "_id": args.username,
            "role": args.role,
            "active": True,
            "salt": salt,
            "passwordHash": password_hash(password, salt),
        }
        document["pendingAudit"] = [
            make_event(None, "USUARIO_CREADO", None, None, user_view(document)),
        ]
        try:
            database.users.insert_one(document)
        except DuplicateKeyError:
            parser.error("El usuario ya existe.")
        publish_collection_pending(database, "users", args.username)
    print(f"Cuenta creada: {args.username} ({args.role})")


if __name__ == "__main__":
    main()
