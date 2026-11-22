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
from pymongo import DESCENDING
from pymongo.errors import PyMongoError

from ai_service.contract import Category
from backend.audit import event_pipeline, make_event, publish_pending, snapshot, update_with_events
from backend.auth import UserIdentity, administrator, current_user, router as auth_router
from backend.users import router as users_router
from backend.classifier import classify
from backend.db import connect, get_database, initialize_database
from backend.filters import date_range
from backend.schemas import (
    AuditPage, ManualClassification, MessageCreated, MessageDetail, MessageInput, MessagePage, MessageSummary,
    MessageStatus, StatusChange,
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
        initialize_database(app.state.db)
        publish_pending(app.state.db)
        yield


app = FastAPI(title="Gestión inteligente de correos", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    if request.url.path == "/api/v1/auth/login":
        return JSONResponse(status_code=422, content={"detail": "Usuario o contraseña con formato inválido."})
    if request.url.path.startswith(("/api/v1/auth/", "/api/v1/users")):
        return JSONResponse(status_code=422, content={"detail": "Revisa los campos y la política de contraseñas."})
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
        revision=0,
    )
    document["pendingAudit"] = [
        make_event(message_id, "MENSAJE_REGISTRADO", user.id, None, snapshot(document)),
    ]
    messages = request.app.state.db.messages
    messages.insert_one(document)
    publish_pending(request.app.state.db, message_id)

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
    updates = {
        "status": status,
        "prediction": prediction.model_dump() if prediction else None,
        "department": department,
        "assignmentOrigin": "IA" if department else None,
        "assignment": {
            "department": department, "source": "IA", "reason": None,
            "timestamp": datetime.now(timezone.utc),
        } if department else None,
    }
    after = snapshot({**document, **updates})
    events = []
    if prediction:
        events.append(make_event(
            message_id, "PREDICCION_REGISTRADA", None, snapshot(document),
            {**snapshot(document), "prediction": prediction.model_dump()},
        ))
    events.append(make_event(
        message_id, action, None,
        {**snapshot(document), "prediction": prediction.model_dump()} if prediction else snapshot(document),
        after,
    ))
    update_with_events(request.app.state.db, document, updates, events)
    return MessageCreated(id=str(message_id), status=status, prediction=prediction, department=department)


@app.get("/api/v1/messages", response_model=MessagePage)
def list_messages(
    request: Request,
    user: Annotated[UserIdentity, Depends(current_user)],
    page: int = Query(default=1, ge=1, le=1_000_000),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    text: str | None = Query(default=None, min_length=1, max_length=160),
    status: MessageStatus | None = None,
    department: Category | None = None,
    date_from: datetime | None = Query(default=None, alias="dateFrom"),
    date_to: datetime | None = Query(default=None, alias="dateTo"),
):
    collection = request.app.state.db.messages
    filters = {}
    if status is not None:
        filters["status"] = status
    if department is not None:
        filters["department"] = department
    dates = date_range(date_from, date_to)
    if dates:
        filters["createdAt"] = dates
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
    db = request.app.state.db
    publish_pending(db, message_id)
    messages = db.messages
    query = {"_id": ObjectId(message_id)}
    before = messages.find_one(query)
    if before is None:
        raise HTTPException(404, "Mensaje no encontrado.")
    if before["status"] not in {"PENDIENTE_REVISION", "PENDIENTE_CLASIFICACION", "CLASIFICADO", "EN_GESTION"}:
        raise HTTPException(409, "El estado actual no admite una asignación manual.")
    updates = {
        "status": "EN_GESTION",
        "department": assignment.department,
        "assignmentOrigin": "MANUAL",
        "assignment": {
            "department": assignment.department,
            "source": "MANUAL",
            "timestamp": datetime.now(timezone.utc),
            "reason": assignment.reason,
        },
    }
    document = update_with_events(
        db, before, updates, [make_event(
            message_id, "CLASIFICACION_MANUAL", user.id,
            snapshot(before), snapshot({**before, **updates}), assignment.reason,
        )],
    )
    return MessageDetail(id=message_id, **document)


@app.patch("/api/v1/messages/{message_id}/status", response_model=MessageDetail)
def change_status(
    message_id: MessageId,
    change: StatusChange,
    request: Request,
    user: Annotated[UserIdentity, Depends(current_user)],
):
    previous, action = {
        "EN_GESTION": ("CLASIFICADO", "GESTION_INICIADA"),
        "CERRADO": ("EN_GESTION", "MENSAJE_CERRADO"),
    }[change.status]
    updates = {
        "status": change.status,
    }
    if change.status == "CERRADO":
        updates["resolution"] = change.reason

    db = request.app.state.db
    publish_pending(db, message_id)
    messages = db.messages
    query = {"_id": ObjectId(message_id)}
    before = messages.find_one(query)
    if before is None:
        raise HTTPException(404, "Mensaje no encontrado.")
    if before["status"] != previous:
        raise HTTPException(409, "El estado actual no admite esta transición.")
    document = update_with_events(
        db, before, updates, [make_event(
            message_id, action, user.id, snapshot(before), snapshot({**before, **updates}), change.reason,
        )],
    )
    return MessageDetail(id=message_id, **document)


@app.get("/api/v1/audit-events", response_model=AuditPage)
def list_audit_events(
    request: Request,
    user: Annotated[UserIdentity, Depends(administrator)],
    message_id: Annotated[str | None, Query(alias="messageId", pattern=r"^[a-f0-9]{24}$")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    actor: str | None = Query(default=None, min_length=1, max_length=64),
    action: str | None = Query(default=None, min_length=1, max_length=128),
    date_from: datetime | None = Query(default=None, alias="dateFrom"),
    date_to: datetime | None = Query(default=None, alias="dateTo"),
):
    filters = {}
    if message_id is not None:
        filters["messageId"] = message_id
    if actor is not None:
        filters["actorUserId"] = actor
    if action is not None:
        filters["action"] = action
    dates = date_range(date_from, date_to)
    if dates:
        filters["createdAt"] = dates
    publish_pending(request.app.state.db, message_id)
    return AuditPage(items=list(request.app.state.db.audit_events.aggregate(event_pipeline(filters, limit))))
