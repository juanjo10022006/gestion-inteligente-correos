FROM python:3.13-slim@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 AS python-base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/requirements.txt /tmp/api-requirements.txt
RUN pip install --no-cache-dir -r /tmp/api-requirements.txt

FROM python-base AS api
COPY backend/ backend/
COPY ai_service/contract.py ai_service/preprocessing.py ai_service/
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python-base AS model-build
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
COPY ai_service/requirements.txt /tmp/model-requirements.txt
RUN pip install --no-cache-dir -r /tmp/model-requirements.txt
COPY ai_service/*.py ai_service/
COPY ai_service/data/correos_sinteticos_v0.3.jsonl ai_service/data/
RUN python -m ai_service.train --output-dir /candidate \
    && python -m ai_service.promote --candidate-dir /candidate --output-dir /model \
    && python -m ai_service.evaluate_artifact --output /model/validation.json

FROM python-base AS ai
COPY ai_service/requirements.txt /tmp/model-requirements.txt
RUN pip install --no-cache-dir -r /tmp/model-requirements.txt
COPY ai_service/*.py ai_service/
COPY ai_service/data/correos_sinteticos_v0.3.jsonl ai_service/data/
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
COPY --from=model-build /model /model
ENV AI_MODEL_PATH=/model/model.joblib
CMD ["python", "-m", "uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8001"]

FROM ai AS notebooks
COPY ai_service/requirements-notebooks.txt /tmp/notebook-requirements.txt
RUN pip install --no-cache-dir -r /tmp/notebook-requirements.txt
COPY ai_service/notebooks/ ai_service/notebooks/
CMD ["python", "-m", "ai_service.run_notebooks", "--output-dir", "/tmp/notebooks-ejecutados"]
