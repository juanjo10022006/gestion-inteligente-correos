from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints, model_validator

from ai_service.contract import Category, Prediction


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
    sender: str | None
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


class MessagePage(BaseModel):
    items: list[MessageSummary]
    page: int
    pageSize: int
    total: int


class AuditEvent(BaseModel):
    action: str
    messageId: str
    actorUserId: str
    createdAt: datetime
    reason: str | None = None


class AuditPage(BaseModel):
    items: list[AuditEvent]
