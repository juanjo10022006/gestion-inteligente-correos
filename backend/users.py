import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, Response
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.access_models import UserCreate, UserCreated, UserPage, UserUpdate, UserView
from backend.audit import make_event, publish_collection_pending
from backend.auth import UserIdentity, administrator

router = APIRouter(prefix="/api/v1/users", tags=["Usuarios"])
temporary_duration = timedelta(hours=24)


def credential_hash(value: str) -> bytes:
    return hashlib.sha256(value.encode()).digest()


def user_view(document: dict) -> dict:
    # Explicit allowlist; never return the Mongo document itself.
    return {
        "id": document["_id"], "username": document["_id"], "role": document["role"],
        "active": document["active"],
        "activated": document.get("activated", "passwordHash" in document),
        "createdAt": document.get("createdAt"),
    }


@router.post("", response_model=UserCreated, status_code=201)
def create_user(
    payload: UserCreate, request: Request, response: Response,
    administrator_user: Annotated[UserIdentity, Depends(administrator)],
):
    db = request.app.state.db
    now = datetime.now(timezone.utc)
    temporary = secrets.token_urlsafe(32)
    expires = now + temporary_duration
    document = {
        "_id": payload.username, "role": payload.role, "active": payload.active,
        "activated": False, "activationCredentialHash": credential_hash(temporary),
        "activationExpiresAt": expires, "createdAt": now, "updatedAt": now,
        "revision": 0, "authVersion": 0,
    }
    document["pendingAudit"] = [
        make_event(None, "USUARIO_CREADO", administrator_user.id, None, user_view(document)),
    ]
    try:
        db.users.insert_one(document)
    except DuplicateKeyError:
        raise HTTPException(409, "El identificador de usuario ya existe.") from None
    publish_collection_pending(db, "users", payload.username)
    response.headers["Cache-Control"] = "no-store"
    return UserCreated(user=UserView(**user_view(document)), temporaryCredential=temporary,
                       credentialExpiresAt=expires)


@router.get("", response_model=UserPage)
def list_users(
    request: Request, response: Response,
    user: Annotated[UserIdentity, Depends(administrator)],
    page: int = Query(default=1, ge=1, le=1_000_000),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
):
    collection = request.app.state.db.users
    # passwordHash existence is represented by activated for legacy accounts.
    projection = {"role": 1, "active": 1, "activated": 1, "createdAt": 1}
    documents = collection.find({}, projection).sort("_id", 1).skip((page - 1) * page_size).limit(page_size)
    items = []
    for document in documents:
        # CLI accounts predate activated; absence means activated (they have a permanent hash).
        document.setdefault("activated", True)
        items.append(UserView(**user_view(document)))
    response.headers["Cache-Control"] = "no-store"
    return UserPage(items=items, page=page, pageSize=page_size, total=collection.count_documents({}))


@router.patch("/{username}", response_model=UserView)
def update_user(
    username: Annotated[str, Path(min_length=1, max_length=64)],
    payload: UserUpdate, request: Request,
    user: Annotated[UserIdentity, Depends(administrator)],
):
    db = request.app.state.db
    publish_collection_pending(db, "users", username)
    before = db.users.find_one({"_id": username})
    if before is None:
        raise HTTPException(404, "Usuario no encontrado.")
    # Avoid accidentally losing the currently authenticated administrator.
    if username == user.id and (not payload.active or payload.role != "ADMINISTRADOR"):
        raise HTTPException(409, "No puedes desactivar ni degradar tu propia cuenta.")
    if before["active"] == payload.active and before["role"] == payload.role:
        return UserView(**user_view(before))
    updates = {"role": payload.role, "active": payload.active, "updatedAt": datetime.now(timezone.utc)}
    event = make_event(None, "USUARIO_ACTUALIZADO", user.id, user_view(before), user_view({**before, **updates}))
    query = {"_id": username, "revision": before.get("revision", {"$exists": False})}
    document = db.users.find_one_and_update(
        query, {"$set": updates, "$inc": {"revision": 1, "authVersion": 1},
                "$push": {"pendingAudit": event}}, return_document=ReturnDocument.AFTER,
    )
    if document is None:
        raise HTTPException(409, "La cuenta cambió durante la operación. Actualiza e intenta de nuevo.")
    publish_collection_pending(db, "users", username)
    return UserView(**user_view(document))
