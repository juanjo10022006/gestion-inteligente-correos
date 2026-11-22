FROM python:3.13-slim AS python-base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/requirements.txt /tmp/api-requirements.txt
RUN pip install --no-cache-dir -r /tmp/api-requirements.txt

FROM python-base AS api
COPY backend/ backend/
COPY ai_service/contract.py ai_service/preprocessing.py ai_service/
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python-base AS ai
COPY ai_service/requirements.txt /tmp/model-requirements.txt
RUN pip install --no-cache-dir -r /tmp/model-requirements.txt
COPY ai_service/contract.py ai_service/preprocessing.py ai_service/train.py ai_service/main.py ai_service/
COPY ai_service/data/correos_sinteticos_v0.3.jsonl ai_service/data/
RUN python -m ai_service.train --output-dir /model && mv /model/*.joblib /model/model.joblib
ENV AI_MODEL_PATH=/model/model.joblib
CMD ["python", "-m", "uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
