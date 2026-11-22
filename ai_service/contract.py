from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

Category = Literal["FACTURACION", "RECURSOS_HUMANOS", "SOPORTE_TECNICO", "VENTAS"]


class PredictionRequest(BaseModel):
    text: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10161)]
    preprocessingVersion: str


class Prediction(BaseModel):
    category: Category
    confidence: Annotated[float, Field(ge=0, le=1, strict=True, allow_inf_nan=False)]
    modelVersion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]
