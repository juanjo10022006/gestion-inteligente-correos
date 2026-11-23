import argparse
import hashlib
from pathlib import Path

import joblib

from ai_service.train import ROOT, load_dataset, routing_summary


def main():
    parser = argparse.ArgumentParser(description="Comparar umbrales con la partición de validación.")
    parser.add_argument("model", type=Path, help="Archivo .joblib generado por el equipo.")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "correos_sinteticos_v0.3.jsonl")
    parser.add_argument("--thresholds", type=float, nargs="+", default=[0.30, 0.40, 0.45, 0.55, 0.70])
    args = parser.parse_args()
    if any(not 0 <= threshold <= 1 for threshold in args.thresholds):
        parser.error("Los umbrales deben estar entre 0 y 1.")

    artifact = joblib.load(args.model)
    raw_data = args.dataset.read_bytes()
    if hashlib.sha256(raw_data).hexdigest() != artifact["metadata"]["datasetSha256"]:
        parser.error("El dataset no coincide con la versión usada para entrenar este modelo.")
    texts, labels = load_dataset(raw_data)["validation"]
    print(f"Modelo: {artifact['metadata']['modelVersion']} | Validación: {len(labels)} correos")
    print(f"{'Umbral':>8} {'Automáticos':>12} {'Cobertura':>10} {'Aciertos':>10} {'Revisión':>9}")
    for threshold in args.thresholds:
        metrics = routing_summary(artifact["pipeline"], texts, labels, threshold)
        automatic = metrics["automaticCount"]
        accuracy = metrics["automaticAccuracy"]
        hits = "—" if accuracy is None else f"{round(accuracy * automatic)}/{automatic}"
        print(f"{threshold:>7.0%} {automatic:>12} {metrics['coverage']:>10.0%} "
              f"{hits:>10} {metrics['reviewCount']:>9}")


if __name__ == "__main__":
    main()
