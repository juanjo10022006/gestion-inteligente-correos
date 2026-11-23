import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, SecretStr
from pymongo import ReturnDocument

from backend.access_models import ActivationInput, Role
from backend.audit import make_event, publish_after_commit

router = APIRouter(prefix="/api/v1/auth", tags=["Acceso"])
bearer = HTTPBearer(auto_error=False)
session_duration = timedelta(hours=1)


class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=256)


class UserIdentity(BaseModel):
    id: str
    role: Role


class LoginResult(BaseModel):
    accessToken: str
    user: UserIdentity


def password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**17, r=8, p=1, maxmem=256 * 1024**2)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def unauthorized():
    return HTTPException(401, "Credenciales o sesión inválidas.", headers={"WWW-Authenticate": "Bearer"})


@router.post("/login", response_model=LoginResult)
def login(credentials: LoginInput, request: Request, response: Response):
    db = request.app.state.db
    user = db.users.find_one({"_id": credentials.username})
    salt = user.get("salt", bytes(16)) if user else bytes(16)
    expected = user.get("passwordHash", bytes(64)) if user else bytes(64)
    valid = hmac.compare_digest(password_hash(credentials.password.get_secret_value(), salt), expected)
    if not valid or not user or not user["active"] or not user.get("activated", True):
        raise unauthorized()

    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session = {
        "_id": token_digest(token),
        "userId": user["_id"],
        "createdAt": now,
        "validUntil": now + session_duration,
        "authVersion": user.get("authVersion", 0),
        "pendingAudit": [make_event(
            None, "SESION_INICIADA", user["_id"], None,
            {"userId": user["_id"], "expiresAt": now + session_duration},
        )],
    }
    db.sessions.insert_one(session)
    publish_after_commit(db, "sessions", session["_id"], response)
    response.headers["Cache-Control"] = "no-store"
    return LoginResult(accessToken=token, user=UserIdentity(id=user["_id"], role=user["role"]))


def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> UserIdentity:
    if credentials is None:
        raise unauthorized()
    db = request.app.state.db
    session = db.sessions.find_one({
        "_id": token_digest(credentials.credentials),
        "$or": [
            {"validUntil": {"$gt": datetime.now(timezone.utc)}},
            {"validUntil": {"$exists": False}, "expiresAt": {"$gt": datetime.now(timezone.utc)}},
        ],
        "revokedAt": {"$exists": False},
    })
    if session is None:
        raise unauthorized()
    user = db.users.find_one({"_id": session["userId"], "active": True})
    if (user is None or not user.get("activated", True)
            or user.get("authVersion", 0) != session.get("authVersion", 0)):
        raise unauthorized()
    return UserIdentity(id=user["_id"], role=user["role"])


def administrator(user: Annotated[UserIdentity, Depends(current_user)]) -> UserIdentity:
    if user.role != "ADMINISTRADOR":
        raise HTTPException(403, "Se requiere el rol ADMINISTRADOR.")
    return user


@router.post("/activate", status_code=204)
def activate(payload: ActivationInput, request: Request):
    # Local import keeps the users router's administrator dependency acyclic.
    from backend.users import credential_hash, user_view
    db = request.app.state.db
    publish_after_commit(db, "users", payload.username)
    now = datetime.now(timezone.utc)
    query = {
        "_id": payload.username, "activated": False, "active": True,
        "activationCredentialHash": credential_hash(payload.temporaryCredential.get_secret_value()),
        "activationExpiresAt": {"$gt": now},
    }
    before = db.users.find_one(query)
    if before is None:
        raise unauthorized()
    salt = secrets.token_bytes(16)
    updates = {
        "salt": salt, "passwordHash": password_hash(payload.newPassword.get_secret_value(), salt),
        "activated": True, "updatedAt": now,
    }
    query["revision"] = before.get("revision", {"$exists": False})
    query["activationExpiresAt"] = {"$gt": datetime.now(timezone.utc)}
    event = make_event(None, "CUENTA_ACTIVADA", payload.username, user_view(before), user_view({**before, **updates}))
    document = db.users.find_one_and_update(
        query,
        {"$set": updates, "$unset": {"activationCredentialHash": "", "activationExpiresAt": ""},
         "$inc": {"revision": 1, "authVersion": 1}, "$push": {"pendingAudit": event}},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise unauthorized()
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    publish_after_commit(db, "users", payload.username, response)
    return response


@router.post("/logout", status_code=204)
def logout(
    request: Request, user: Annotated[UserIdentity, Depends(current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
):
    db = request.app.state.db
    identifier = token_digest(credentials.credentials)
    now = datetime.now(timezone.utc)
    session = db.sessions.find_one({"_id": identifier})
    if session is None:
        raise unauthorized()
    event = make_event(None, "SESION_CERRADA", user.id, {"userId": user.id, "revoked": False},
                       {"userId": user.id, "revoked": True})
    result = db.sessions.update_one(
        {"_id": identifier, "revokedAt": {"$exists": False}},
        {"$set": {"revokedAt": now, "validUntil": session.get("validUntil", session.get("expiresAt"))},
         "$unset": {"expiresAt": ""}, "$push": {"pendingAudit": event}},
    )
    if not result.matched_count:
        raise unauthorized()
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    publish_after_commit(db, "sessions", identifier, response)
    return response
