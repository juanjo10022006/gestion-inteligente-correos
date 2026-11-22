import os

from pymongo import MongoClient


def connect():
    uri = os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017")
    return MongoClient(uri, serverSelectionTimeoutMS=2000, tz_aware=True)


def get_database(client):
    return client[os.environ.get("MONGODB_DB_NAME", "gestion_correos")]
