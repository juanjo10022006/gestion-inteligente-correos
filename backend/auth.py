import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, SecretStr

Role = Literal["OPERADOR", "ADMINISTRADOR"]
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
    salt = user["salt"] if user else bytes(16)
    expected = user["passwordHash"] if user else bytes(64)
    valid = hmac.compare_digest(password_hash(credentials.password.get_secret_value(), salt), expected)
    if not valid or not user or not user["active"]:
        raise unauthorized()

    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    db.sessions.insert_one({
        "_id": token_digest(token),
        "userId": user["_id"],
        "createdAt": now,
        "expiresAt": now + session_duration,
    })
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
        "expiresAt": {"$gt": datetime.now(timezone.utc)},
    })
    if session is None:
        raise unauthorized()
    user = db.users.find_one({"_id": session["userId"], "active": True})
    if user is None:
        raise unauthorized()
    return UserIdentity(id=user["_id"], role=user["role"])


def administrator(user: Annotated[UserIdentity, Depends(current_user)]) -> UserIdentity:
    if user.role != "ADMINISTRADOR":
        raise HTTPException(403, "Se requiere el rol ADMINISTRADOR.")
    return user
