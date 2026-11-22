import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import PyMongoError

from backend.auth import UserIdentity, administrator, current_user, router as auth_router
from backend.classifier import classify
from backend.db import connect, get_database
from backend.schemas import (
    AuditPage, ManualClassification, MessageCreated, MessageDetail, MessageInput, MessagePage, MessageSummary,
    StatusChange,
)

ROUTING_THRESHOLD = 0.70
MessageId = Annotated[str, Path(pattern=r"^[a-f0-9]{24}$")]


@asynccontextmanager
async def lifespan(app: FastAPI):
    threshold = float(os.environ.get("ROUTING_THRESHOLD", str(ROUTING_THRESHOLD)))
    if not 0 <= threshold <= 1:
        raise ValueError("ROUTING_THRESHOLD debe estar entre 0 y 1.")
    app.state.routing_threshold = threshold
    with connect() as client:
        app.state.db = get_database(client)
        app.state.db.sessions.create_index("expiresAt", expireAfterSeconds=0)
        yield


app = FastAPI(title="Gestión inteligente de correos", lifespan=lifespan)
app.include_router(auth_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    if request.url.path == "/api/v1/auth/login":
        return JSONResponse(status_code=422, content={"detail": "Usuario o contraseña con formato inválido."})
    return await request_validation_exception_handler(request, error)


@app.exception_handler(PyMongoError)
async def database_error(request: Request, error: PyMongoError):
    return JSONResponse(status_code=503, content={"detail": "No se pudo completar la operación en MongoDB."})


@app.post("/api/v1/messages", response_model=MessageCreated, status_code=201)
def register_message(message: MessageInput, request: Request, user: Annotated[UserIdentity, Depends(current_user)]):
    message_id = ObjectId()
    now = datetime.now(timezone.utc)
    document = message.model_dump()
    document.update(
        _id=message_id,
        status="RECIBIDO",
        createdAt=now,
        createdBy=user.id,
        creationEvent={
            "action": "MENSAJE_REGISTRADO",
            "messageId": str(message_id),
            "actorUserId": user.id,
            "createdAt": now,
        },
    )
    messages = request.app.state.db.messages
    messages.insert_one(document)

    prediction = classify(message.subject, message.body)
    department = None
    if prediction is None:
        status = "PENDIENTE_CLASIFICACION"
        action = "CLASIFICACION_NO_DISPONIBLE"
    elif prediction.confidence < request.app.state.routing_threshold:
        status = "PENDIENTE_REVISION"
        action = "CLASIFICACION_EN_REVISION"
    else:
        status = "CLASIFICADO"
        department = prediction.category
        action = "MENSAJE_CLASIFICADO"
    messages.update_one({"_id": message_id}, {"$set": {
        "status": status,
        "prediction": prediction.model_dump() if prediction else None,
        "department": department,
        "classificationEvent": {
            "action": action,
            "messageId": str(message_id),
            "actorUserId": "SISTEMA",
            "createdAt": datetime.now(timezone.utc),
        },
    }})
    return MessageCreated(id=str(message_id), status=status, prediction=prediction, department=department)


@app.get("/api/v1/messages", response_model=MessagePage)
def list_messages(
    request: Request,
    user: Annotated[UserIdentity, Depends(current_user)],
    page: int = Query(default=1, ge=1, le=1_000_000),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    text: str | None = Query(default=None, min_length=1, max_length=160),
):
    collection = request.app.state.db.messages
    filters = {}
    if text:
        pattern = re.compile(re.escape(text), re.IGNORECASE)
        filters["$or"] = [{field: pattern} for field in ("subject", "body")]

    documents = (
        collection.find(filters, {"subject": 1, "sender": 1, "status": 1, "createdAt": 1,
                                  "prediction": 1, "department": 1})
        .sort([("createdAt", DESCENDING), ("_id", DESCENDING)])
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    items = [
        MessageSummary(
            id=str(document["_id"]),
            subject=document["subject"],
            sender=document.get("sender"),
            status=document["status"],
            createdAt=document["createdAt"],
            prediction=document.get("prediction"),
            department=document.get("department"),
        )
        for document in documents
    ]
    return MessagePage(items=items, page=page, pageSize=page_size, total=collection.count_documents(filters))


@app.get("/api/v1/messages/{message_id}", response_model=MessageDetail)
def get_message(message_id: MessageId, request: Request, user: Annotated[UserIdentity, Depends(current_user)]):
    document = request.app.state.db.messages.find_one({"_id": ObjectId(message_id)})
    if document is None:
        raise HTTPException(404, "Mensaje no encontrado.")
    return MessageDetail(id=message_id, **document)


@app.patch("/api/v1/messages/{message_id}/classification", response_model=MessageDetail)
def assign_department(
    message_id: MessageId,
    assignment: ManualClassification,
    request: Request,
    user: Annotated[UserIdentity, Depends(current_user)],
):
    messages = request.app.state.db.messages
    query = {"_id": ObjectId(message_id)}
    document = messages.find_one_and_update(
        {**query, "status": {"$in": ["PENDIENTE_REVISION", "PENDIENTE_CLASIFICACION", "CLASIFICADO"]}},
        {"$set": {
            "status": "EN_GESTION",
            "department": assignment.department,
            "assignmentOrigin": "MANUAL",
            "manualEvent": {
                "action": "CLASIFICACION_MANUAL",
                "messageId": message_id,
                "actorUserId": user.id,
                "createdAt": datetime.now(timezone.utc),
                "reason": assignment.reason,
            },
        }},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        if messages.find_one(query, {"_id": 1}) is None:
            raise HTTPException(404, "Mensaje no encontrado.")
        raise HTTPException(409, "El estado actual no admite una asignación manual.")
    return MessageDetail(id=message_id, **document)


@app.patch("/api/v1/messages/{message_id}/status", response_model=MessageDetail)
def change_status(
    message_id: MessageId,
    change: StatusChange,
    request: Request,
    user: Annotated[UserIdentity, Depends(current_user)],
):
    previous, action, event_field = {
        "EN_GESTION": ("CLASIFICADO", "GESTION_INICIADA", "managementEvent"),
        "CERRADO": ("EN_GESTION", "MENSAJE_CERRADO", "closureEvent"),
    }[change.status]
    updates = {
        "status": change.status,
        event_field: {
            "action": action,
            "messageId": message_id,
            "actorUserId": user.id,
            "createdAt": datetime.now(timezone.utc),
            "reason": change.reason,
        },
    }
    if change.status == "CERRADO":
        updates["resolution"] = change.reason

    messages = request.app.state.db.messages
    query = {"_id": ObjectId(message_id)}
    document = messages.find_one_and_update(
        {**query, "status": previous},
        {"$set": updates},
        return_document=ReturnDocument.AFTER,
    )
    if document is None:
        if messages.find_one(query, {"_id": 1}) is None:
            raise HTTPException(404, "Mensaje no encontrado.")
        raise HTTPException(409, "El estado actual no admite esta transición.")
    return MessageDetail(id=message_id, **document)


@app.get("/api/v1/audit-events", response_model=AuditPage)
def list_audit_events(
    request: Request,
    user: Annotated[UserIdentity, Depends(administrator)],
    message_id: Annotated[str | None, Query(alias="messageId", pattern=r"^[a-f0-9]{24}$")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    filters = {"creationEvent": {"$exists": True}}
    if message_id is not None:
        filters["_id"] = ObjectId(message_id)
    events = request.app.state.db.messages.aggregate([
        {"$match": filters},
        {"$project": {"events": [
            "$creationEvent",
            {"$ifNull": ["$classificationEvent", None]},
            {"$ifNull": ["$manualEvent", None]},
            {"$ifNull": ["$managementEvent", None]},
            {"$ifNull": ["$closureEvent", None]},
        ]}},
        {"$unwind": "$events"},
        {"$match": {"events": {"$ne": None}}},
        {"$sort": {"events.createdAt": -1, "_id": -1, "events.action": 1}},
        {"$limit": limit},
    ])
    return AuditPage(items=[document["events"] for document in events])
