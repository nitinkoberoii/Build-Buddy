"""Database engine, sessionmaker, and FastAPI dependency."""
import os
import pathlib
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from api.config import DATABASE_URL

# Ensure parent directory exists if using SQLite file path
if DATABASE_URL.startswith("sqlite:///"):
    db_relative_path = DATABASE_URL.replace("sqlite:///", "")
    if db_relative_path != ":memory:":
        db_file_path = pathlib.Path(db_relative_path)
        db_file_path.parent.mkdir(parents=True, exist_ok=True)

# Connection arguments (SQLite requires check_same_thread=False for FastAPI concurrency)
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
