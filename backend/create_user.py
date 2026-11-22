from argparse import ArgumentParser
from getpass import getpass
from secrets import token_bytes

from pymongo.errors import DuplicateKeyError

from backend.auth import password_hash
from backend.db import connect, get_database


def main():
    parser = ArgumentParser(description="Crear una cuenta de prueba activa para el entorno local.")
    parser.add_argument("username")
    parser.add_argument("role", choices=("OPERADOR", "ADMINISTRADOR"))
    args = parser.parse_args()
    if not 1 <= len(args.username) <= 64 or not all(c.isalnum() or c in "._-" for c in args.username):
        parser.error("El usuario debe contener entre 1 y 64 letras, números o caracteres ._-")
    password = getpass("Contraseña nueva: ")
    if not 12 <= len(password) <= 256 or not password.strip():
        parser.error("La contraseña debe tener entre 12 y 256 caracteres y no estar en blanco.")
    if password != getpass("Repite la contraseña: "):
        parser.error("Las contraseñas no coinciden.")
    salt = token_bytes(16)
    with connect() as client:
        try:
            get_database(client).users.insert_one({
                "_id": args.username,
                "role": args.role,
                "active": True,
                "salt": salt,
                "passwordHash": password_hash(password, salt),
            })
        except DuplicateKeyError:
            parser.error("El usuario ya existe.")
    print(f"Cuenta creada: {args.username} ({args.role})")


if __name__ == "__main__":
    main()
