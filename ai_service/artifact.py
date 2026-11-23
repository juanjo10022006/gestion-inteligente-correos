"""Verify only locally generated/trusted joblib artifacts; hashes are not signatures."""
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

import joblib

from ai_service import preprocessing
from ai_service.preprocessing import PREPROCESSING_VERSION


def load_verified(model_path, manifest_path=None):
    path = Path(model_path)
    manifest = json.loads(Path(manifest_path or path.with_name("manifest.json")).read_text(encoding="utf-8"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest["artifactSha256"]:
        raise ValueError("El artefacto no coincide con su manifiesto.")
    artifact = joblib.load(path)
    metadata = artifact["metadata"]
    if metadata["modelVersion"] != manifest["modelVersion"]:
        raise ValueError("La versión del manifiesto no coincide con el modelo.")
    if metadata["python"] != platform.python_version():
        raise ValueError("La versión Python no coincide con la usada para entrenar.")
    for name, expected in metadata["dependencies"].items():
        if version(name) != expected:
            raise ValueError(f"Dependencia incompatible: {name}.")
    if metadata["preprocessingVersion"] != PREPROCESSING_VERSION:
        raise ValueError("Versión de preprocesamiento incompatible.")
    code_hash = hashlib.sha256(Path(preprocessing.__file__).read_bytes()).hexdigest()
    if metadata["preprocessingCodeSha256"] != code_hash:
        raise ValueError("El código de preprocesamiento no coincide con el artefacto.")
    if tuple(artifact["pipeline"].classes_) != tuple(metadata["classes"]):
        raise ValueError("Las clases del pipeline no coinciden con sus metadatos.")
    return artifact, manifest
