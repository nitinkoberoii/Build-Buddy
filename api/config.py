import os
import pathlib
from typing import List

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / os.getenv("STORAGE_DIR", "storage/generations")

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
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

PROJECT_NAME = "BuildBuddy API"
API_VERSION = "v1"
