from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StringConstraints, field_validator

Role = Literal["OPERADOR", "ADMINISTRADOR"]
Username = Annotated[str, StringConstraints(
    strip_whitespace=True, min_length=1, max_length=64, pattern=r"^[A-Za-z0-9._-]+$",
)]


def validate_password(password: str) -> str:
    if not 12 <= len(password) <= 256 or not password.strip():
        raise ValueError("La contraseña debe contener entre 12 y 256 caracteres y no estar en blanco.")
    return password


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    role: Role
    active: bool = Field(default=True, strict=True)


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role
    active: bool = Field(strict=True)


class UserView(BaseModel):
    id: str
    username: str
    role: Role
    active: bool
    activated: bool
    createdAt: datetime | None = None


class UserCreated(BaseModel):
    user: UserView
    temporaryCredential: str
    credentialExpiresAt: datetime


class UserPage(BaseModel):
    items: list[UserView]
    page: int
    pageSize: int
    total: int


class ActivationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    temporaryCredential: SecretStr = Field(min_length=1, max_length=128)
    newPassword: SecretStr = Field(min_length=12, max_length=256)

    @field_validator("newPassword")
    @classmethod
    def password_policy(cls, value: SecretStr) -> SecretStr:
        validate_password(value.get_secret_value())
        return value
