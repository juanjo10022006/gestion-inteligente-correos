import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from sklearn.dummy import DummyClassifier

from ai_service.artifact import load_verified
from ai_service.train import ROOT, THRESHOLD, evaluate, load_dataset, routing_summary


def evaluate_frozen(model_path, dataset, include_test=False):
    artifact, manifest = load_verified(model_path)
    raw = Path(dataset).read_bytes()
    if hashlib.sha256(raw).hexdigest() != artifact["metadata"]["datasetSha256"]:
        raise ValueError("El dataset no coincide con el artefacto.")
    partitions = load_dataset(raw)
    baseline = DummyClassifier(strategy="most_frequent").fit(*partitions["train"])
    pipeline = artifact["pipeline"]
    evaluations = {}
    errors = {}
    for split in (("validation", "test") if include_test else ("validation",)):
        texts, labels = partitions[split]
        evaluations[split] = {
            "baseline": evaluate(baseline, texts, labels),
            "classifier": evaluate(pipeline, texts, labels),
            "routingSimulation": routing_summary(pipeline, texts, labels, THRESHOLD),
        }
        rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if json.loads(line)["split"] == split]
        predictions = pipeline.predict(texts)
        errors[split] = [{"id": row["id"], "expected": expected, "predicted": str(prediction)}
                         for row, expected, prediction in zip(rows, labels, predictions, strict=True)
                         if prediction != expected]
    return {
        **artifact["metadata"], **manifest, "thresholdProvisional": THRESHOLD,
        "evaluations": evaluations, "errors": errors,
        "validationThresholds": [
            routing_summary(pipeline, *partitions["validation"], threshold)
            for threshold in (0.30, 0.40, 0.45, 0.55, 0.70)
        ],
        "limitations": "128 mensajes sintéticos; test ya evaluado anteriormente, sin nueva selección con test.",
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluar el artefacto congelado sin reentrenar.")
    parser.add_argument("--model", type=Path, default=Path("/model/model.joblib"))
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/correos_sinteticos_v0.3.jsonl")
    parser.add_argument("--include-test", action="store_true")
    parser.add_argument("--service-url", help="Contrastar /health con el modelo evaluado.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate_frozen(args.model, args.dataset, args.include_test)
    if args.service_url:
        with urlopen(args.service_url.rstrip("/") + "/health", timeout=5) as response:
            served = json.load(response)
        if (served["modelVersion"], served["artifactSha256"]) != (report["modelVersion"], report["artifactSha256"]):
            raise ValueError("El servicio no está sirviendo el artefacto evaluado.")
        report["servedArtifactVerified"] = True
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
