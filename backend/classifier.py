import logging
import os
from http.client import HTTPException
from urllib.request import Request, urlopen

from ai_service.contract import Prediction, PredictionRequest
from ai_service.preprocessing import PREPROCESSING_VERSION, prepare_text

logger = logging.getLogger(__name__)


def classify(subject: str, body: str) -> Prediction | None:
    url = os.environ.get("AI_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
    payload = PredictionRequest(text=prepare_text(subject, body), preprocessingVersion=PREPROCESSING_VERSION)
    try:
        request = Request(
            f"{url}/predict",
            data=payload.model_dump_json().encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            return Prediction.model_validate_json(response.read(4096))
    except (OSError, ValueError, HTTPException) as error:
        logger.warning("Clasificación no disponible (%s).", type(error).__name__)
        return None
