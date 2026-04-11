"""Application settings from environment variables."""

import os


def _read_int(name: str, default: str) -> int:
    return int(os.environ.get(name, default))


def _read_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


API_KEY: str = _read_str("API_KEY", "")
TMP_DIR: str = _read_str("TMP_DIR", "/tmp")
TEMPLATES_DIR: str = _read_str("TEMPLATES_DIR", "/templates")
FONTS_DIR: str = _read_str("FONTS_DIR", "/fonts")
MAX_UPLOAD_MB: int = _read_int("MAX_UPLOAD_MB", "100")
WORKERS: int = _read_int("WORKERS", "2")
