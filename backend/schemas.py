from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, StringConstraints, model_validator

from ai_service.contract import Category, Prediction

MessageStatus = Literal[
    "RECIBIDO", "PENDIENTE_CLASIFICACION", "PENDIENTE_REVISION",
    "CLASIFICADO", "EN_GESTION", "CERRADO",
]

class MessageInput(BaseModel):
    subject: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=160)]
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=10_000)]
    sender: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = None


class MessageCreated(BaseModel):
    id: str
    status: str
    prediction: Prediction | None = None
    department: Category | None = None


class MessageSummary(MessageCreated):
    subject: str
    sender: str | None = None
    createdAt: datetime


class ManualClassification(BaseModel):
    department: Category
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=500)]


class StatusChange(BaseModel):
    status: Literal["EN_GESTION", "CERRADO"]
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=500)] | None = None

    @model_validator(mode="after")
    def require_resolution(self):
        if self.status == "CERRADO" and self.reason is None:
            raise ValueError("Indica una resolución para cerrar el correo.")
        return self


class MessageDetail(MessageSummary):
    body: str
    resolution: str | None = None
    assignmentOrigin: Literal["IA", "MANUAL"] | None = None
    assignment: dict[str, Any] | None = None


class MessagePage(BaseModel):
    items: list[MessageSummary]
    page: int
    pageSize: int
    total: int


class AuditEvent(BaseModel):
    id: str
    action: str
    messageId: str | None = None
    actorUserId: str
    actorType: Literal["SISTEMA", "USUARIO"]
    createdAt: datetime
    reason: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    source: Literal["HISTORICAL", "LEGACY"]


class AuditPage(BaseModel):
    items: list[AuditEvent]
