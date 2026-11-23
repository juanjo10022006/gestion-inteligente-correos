"""Small-corpus academic analysis shared by notebooks; no runtime Jupyter dependency."""
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path

from ai_service.preprocessing import prepare_text
from ai_service.train import load_dataset


def environment_report():
    return {"python": platform.python_version(), "dependencies": {
        name: version(name) for name in ("scikit-learn", "numpy", "scipy", "joblib", "pandas", "matplotlib",
                                        "nbformat", "nbclient", "ipykernel")
    }}


def dataset_frame(dataset):
    import pandas as pd
    raw = Path(dataset).read_bytes()
    load_dataset(raw)  # Same checks as training; never silently repair the source corpus.
    frame = pd.DataFrame(json.loads(line) for line in raw.decode("utf-8").splitlines())
    frame["text"] = [prepare_text(row.subject, row.body) for row in frame.itertuples()]
    frame["characters"] = frame["text"].str.len()
    profile = {
        "sha256": hashlib.sha256(raw).hexdigest(), "rows": len(frame),
        "missing": int(frame.isna().sum().sum()),
        "duplicateIds": int(frame["id"].duplicated().sum()),
        "duplicateTexts": int(frame["text"].str.casefold().duplicated().sum()),
        "normalizedRows": int(sum((row.subject + " " + row.body) != row.text for row in frame.itertuples())),
    }
    return frame, profile
