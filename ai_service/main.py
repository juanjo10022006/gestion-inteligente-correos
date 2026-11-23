import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request

from ai_service.contract import Prediction, PredictionRequest
from ai_service.preprocessing import PREPROCESSING_VERSION
from ai_service.artifact import load_verified


@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = Path(os.environ["AI_MODEL_PATH"])
    artifact, manifest = load_verified(model_path)
    if artifact["metadata"]["preprocessingVersion"] != PREPROCESSING_VERSION:
        raise RuntimeError("El modelo usa una versión de preprocesamiento incompatible.")
    app.state.pipeline = artifact["pipeline"]
    app.state.model_version = artifact["metadata"]["modelVersion"]
    app.state.artifact_sha256 = manifest["artifactSha256"]
    yield


app = FastAPI(title="Clasificador interno de correos", lifespan=lifespan)


@app.get("/health")
def health(request: Request):
    return {"modelVersion": request.app.state.model_version, "artifactSha256": request.app.state.artifact_sha256}


@app.post("/predict", response_model=Prediction)
def predict(payload: PredictionRequest, request: Request):
    if payload.preprocessingVersion != PREPROCESSING_VERSION:
        raise HTTPException(422, "Versión de preprocesamiento incompatible.")
    pipeline = request.app.state.pipeline
    probabilities = pipeline.predict_proba([payload.text])[0]
    best = int(probabilities.argmax())
    return Prediction(
        category=str(pipeline.classes_[best]),
        confidence=float(probabilities[best]),
        modelVersion=request.app.state.model_version,
    )
