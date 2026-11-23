import argparse
import json
import os
from pathlib import Path

import nbformat
from nbclient import NotebookClient

from ai_service.train import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    os.environ["NLP_NOTEBOOK_OUTPUT"] = str(args.output_dir.resolve())
    results = []
    sources = sorted((ROOT / "notebooks").glob("*.ipynb"))
    expected = {"00_verificacion_entorno.ipynb", "01_eda_dataset.ipynb", "02_entrenamiento_evaluacion.ipynb"}
    if {source.name for source in sources} != expected:
        raise ValueError("Se requieren exactamente los tres notebooks académicos.")
    for source in sources:
        notebook = nbformat.read(source, as_version=4)
        nbformat.validate(notebook)
        NotebookClient(notebook, timeout=300, kernel_name="python3",
                       resources={"metadata": {"path": str(ROOT.parent)}}).execute()
        nbformat.write(notebook, args.output_dir / source.name)
        results.append({"notebook": source.name, "executedCells": sum(
            cell.cell_type == "code" and cell.execution_count is not None for cell in notebook.cells),
            "errors": sum(output.output_type == "error" for cell in notebook.cells
                          if cell.cell_type == "code" for output in cell.outputs)})
    (args.output_dir / "execution.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results))


if __name__ == "__main__":
    main()
