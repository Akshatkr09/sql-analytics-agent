"""SQLAlchemy engine helpers."""
from functools import lru_cache
from pathlib import Path
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./data/analytics.db")

@lru_cache(maxsize=4)
def get_engine(database_url: str | None = None):
    url = database_url or get_database_url()
    if url.startswith("sqlite:///") and ":memory:" not in url:
        path = Path(url.removeprefix("sqlite:///"))
        if not path.is_absolute():
            path = Path.cwd() / path
        path.parent.mkdir(parents=True, exist_ok=True)
    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=args, future=True)
