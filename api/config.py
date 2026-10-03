import os
import pathlib
from typing import List

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
storage_env = os.getenv("STORAGE_DIR", "storage/generations")
STORAGE_DIR = (
    pathlib.Path(storage_env)
    if pathlib.Path(storage_env).is_absolute()
    else BASE_DIR / storage_env
)

ALLOWED_MODELS: List[str] = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
]

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-oss-20b")
DEFAULT_RECURSION_LIMIT = int(os.getenv("DEFAULT_RECURSION_LIMIT", "100"))

CORS_ORIGINS: List[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

PROJECT_NAME = "BuildBuddy API"
API_VERSION = "v1"
