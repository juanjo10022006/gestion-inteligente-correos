"""Promote a single generated candidate into a checksummed serving bundle."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import joblib

from ai_service.artifact import load_verified


def promote(candidate, output):
    candidate, output = Path(candidate), Path(output)
    artifact = joblib.load(candidate)  # Only the trusted local training output.
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "modelVersion": artifact["metadata"]["modelVersion"],
        "artifactSha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
    }
    shutil.copyfile(candidate, output / "model.joblib")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    load_verified(output / "model.joblib")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    candidates = list(args.candidate_dir.glob("*.joblib"))
    if len(candidates) != 1:
        raise ValueError("Se requiere exactamente un candidato local.")
    print(json.dumps(promote(candidates[0], args.output_dir)))


if __name__ == "__main__":
    main()
