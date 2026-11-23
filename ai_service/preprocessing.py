PREPROCESSING_VERSION = "1"


def prepare_text(subject: str, body: str) -> str:
    return " ".join(f"{subject} {body}".split())
