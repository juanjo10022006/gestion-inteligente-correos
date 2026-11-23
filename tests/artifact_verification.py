import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np

from ai_service.artifact import load_verified
from ai_service.train import ROOT, load_dataset, train


def main():
    served, manifest = load_verified("/model/model.joblib")
    dataset = ROOT / "data/correos_sinteticos_v0.3.jsonl"
    with tempfile.TemporaryDirectory(prefix="artifact-test-") as directory:
        model, _ = train(dataset, Path(directory) / "candidate", False)
        reproduced = joblib.load(model)
        assert reproduced["metadata"]["modelVersion"] == served["metadata"]["modelVersion"]
        texts, _ = load_dataset(dataset.read_bytes())["validation"]
        np.testing.assert_allclose(reproduced["pipeline"].predict_proba(texts),
                                   served["pipeline"].predict_proba(texts), rtol=0, atol=1e-12)
        assert reproduced["pipeline"]["tfidf"].vocabulary_ == served["pipeline"]["tfidf"].vocabulary_
        np.testing.assert_allclose(reproduced["pipeline"]["tfidf"].idf_,
                                   served["pipeline"]["tfidf"].idf_, rtol=0, atol=1e-12)
        np.testing.assert_allclose(reproduced["pipeline"]["classifier"].coef_,
                                   served["pipeline"]["classifier"].coef_, rtol=0, atol=1e-12)
        assert hashlib.sha256(Path("/model/model.joblib").read_bytes()).hexdigest() == manifest["artifactSha256"]
        tampered = Path(directory) / "model.joblib"
        tampered.write_bytes(model.read_bytes() + b"alterado")
        with patch("ai_service.artifact.joblib.load") as unsafe_load:
            try:
                load_verified(tampered, "/model/manifest.json")
            except ValueError:
                pass
            else:
                raise AssertionError("Se aceptó un artefacto con checksum incorrecto.")
            unsafe_load.assert_not_called()
        # Even a checksummed local bundle must match the runtime compatibility metadata.
        for field, incompatible in (("python", "0.0.0"), ("preprocessingVersion", "incompatible"),
                                    ("preprocessingCodeSha256", "0" * 64), ("classes", ["OTRO"])):
            candidate = {**served, "metadata": {**served["metadata"], field: incompatible}}
            joblib.dump(candidate, tampered)
            local_manifest = Path(directory) / "manifest.json"
            local_manifest.write_text(json.dumps({
                **manifest, "artifactSha256": hashlib.sha256(tampered.read_bytes()).hexdigest(),
            }), encoding="utf-8")
            try:
                load_verified(tampered)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Se aceptó metadato incompatible: {field}")
    print("Reproducción funcional, predicciones coincidentes e integridad del artefacto promovido: OK")


if __name__ == "__main__":
    main()
