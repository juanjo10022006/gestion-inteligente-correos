import argparse
import hashlib
import json
import platform
from collections import Counter
from importlib.metadata import version
from pathlib import Path

import joblib
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, log_loss
from sklearn.pipeline import Pipeline

from ai_service.preprocessing import PREPROCESSING_VERSION, prepare_text

ROOT = Path(__file__).resolve().parent
LABELS = ("FACTURACION", "RECURSOS_HUMANOS", "SOPORTE_TECNICO", "VENTAS")
SPLITS = ("train", "validation", "test")
SEED = 42
THRESHOLD = 0.45
VECTORIZER = {"strip_accents": "unicode", "ngram_range": (1, 2)}
CLASSIFIER = {"max_iter": 1000, "random_state": SEED}
CANDIDATE_C = (0.5, 1.0, 3.0, 10.0, 30.0)


def load_dataset(raw_data):
    partitions = {split: ([], []) for split in SPLITS}
    ids = set()
    texts = set()
    for number, line in enumerate(raw_data.decode("utf-8").splitlines(), start=1):
        try:
            row = json.loads(line)
            identifier = row["id"]
            subject, body = row["subject"], row["body"]
            label, split = row["label"], row["split"]
            if not all(isinstance(value, str) and value.strip() for value in (identifier, subject, body)):
                raise ValueError("ID, asunto y cuerpo deben ser textos no vacíos")
            if label not in LABELS or split not in SPLITS:
                raise ValueError("etiqueta o partición desconocida")
            text = prepare_text(subject, body)
            fingerprint = text.casefold()
            if identifier in ids or fingerprint in texts:
                raise ValueError("ID o texto duplicado")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Línea {number}: {error}") from error
        ids.add(identifier)
        texts.add(fingerprint)
        partitions[split][0].append(text)
        partitions[split][1].append(label)

    for split, (_, labels) in partitions.items():
        if set(labels) != set(LABELS):
            raise ValueError(f"La partición {split} debe contener las cuatro categorías.")
    return partitions


def evaluate(model, texts, labels):
    predictions = model.predict(texts)
    return {
        "accuracy": accuracy_score(labels, predictions),
        "macroF1": f1_score(labels, predictions, labels=LABELS, average="macro", zero_division=0),
        "perClass": {
            label: metrics
            for label, metrics in classification_report(
                labels, predictions, labels=LABELS, output_dict=True, zero_division=0
            ).items()
            if label in LABELS
        },
        "confusionMatrix": confusion_matrix(labels, predictions, labels=LABELS).tolist(),
    }


def routing_summary(model, texts, labels, threshold=THRESHOLD):
    probabilities = model.predict_proba(texts)
    accepted = [
        model.classes_[scores.argmax()] == expected
        for scores, expected in zip(probabilities, labels, strict=True)
        if scores.max() >= threshold
    ]
    return {
        "threshold": threshold,
        "automaticCount": len(accepted),
        "reviewCount": len(labels) - len(accepted),
        "coverage": len(accepted) / len(labels),
        "automaticAccuracy": sum(accepted) / len(accepted) if accepted else None,
    }


def train(dataset, output_dir, evaluate_test):
    raw_data = dataset.read_bytes()
    partitions = load_dataset(raw_data)
    train_texts, train_labels = partitions["train"]
    validation_texts, validation_labels = partitions["validation"]
    baseline = DummyClassifier(strategy="most_frequent").fit(train_texts, train_labels)
    candidates = []
    for c in CANDIDATE_C:
        parameters = {**CLASSIFIER, "C": c}
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(**VECTORIZER)),
            ("classifier", LogisticRegression(**parameters)),
        ]).fit(train_texts, train_labels)
        metrics = {
            "C": c,
            "macroF1": f1_score(validation_labels, pipeline.predict(validation_texts), labels=LABELS,
                               average="macro", zero_division=0),
            "logLoss": log_loss(validation_labels, pipeline.predict_proba(validation_texts), labels=LABELS),
        }
        candidates.append((metrics, parameters, pipeline))
    _, parameters, classifier = min(candidates, key=lambda candidate: (
        -candidate[0]["macroF1"], candidate[0]["logLoss"], candidate[0]["C"],
    ))

    metadata = {
        "datasetSha256": hashlib.sha256(raw_data).hexdigest(),
        "preprocessingVersion": PREPROCESSING_VERSION,
        "trainingCodeSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(),
        "dependencies": {
            name: version(name)
            for name in ("scikit-learn", "numpy", "scipy", "joblib", "threadpoolctl", "narwhals")
        },
        "classes": LABELS,
        "vectorizer": VECTORIZER,
        "classifier": parameters,
    }
    fingerprint = hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest()
    model_version = f"tfidf-logreg-{fingerprint[:16]}"
    metadata["modelVersion"] = model_version
    report = {
        **metadata,
        "dataset": dataset.name,
        "splitCounts": {split: dict(Counter(labels)) for split, (_, labels) in partitions.items()},
        "baselineStrategy": "most_frequent",
        "validationCandidates": [metrics for metrics, _, _ in candidates],
        "evaluations": {},
    }
    for split in (("validation", "test") if evaluate_test else ("validation",)):
        texts, labels = partitions[split]
        report["evaluations"][split] = {
            "baseline": evaluate(baseline, texts, labels),
            "classifier": evaluate(classifier, texts, labels),
            "routingSimulation": routing_summary(classifier, texts, labels),
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    model_file = output_dir / f"{model_version}.joblib"
    report_suffix = "validation-test" if evaluate_test else "validation"
    report_file = output_dir / f"{model_version}-{report_suffix}.json"
    joblib.dump({"pipeline": classifier, "metadata": metadata}, model_file, compress=3)
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Modelo: {model_file}")
    print(f"Informe: {report_file}")
    for split, metrics in report["evaluations"].items():
        print(f"{split}: Macro-F1 base={metrics['baseline']['macroF1']:.3f}, "
              f"clasificador={metrics['classifier']['macroF1']:.3f}, "
              f"cobertura a {THRESHOLD:.2f}={metrics['routingSimulation']['coverage']:.1%}")


def main():
    parser = argparse.ArgumentParser(description="Entrenar y evaluar el clasificador de correos.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "correos_sinteticos_v0.3.jsonl")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts")
    parser.add_argument("--evaluate-test", action="store_true", help="Evaluar también el test reservado.")
    args = parser.parse_args()
    try:
        train(args.dataset, args.output_dir, args.evaluate_test)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
