from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, List, Dict, Any

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Numeric,
    insert,
    select,
    delete,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .config import load_settings


metadata = MetaData()

acquisition_metadata = Table(
    "acquisition_metadata",
    metadata,
    Column("run_id", Integer, primary_key=True, autoincrement=True),
    Column("url", Text, nullable=False),
    Column("file_name", Text, nullable=True),
    Column("depth", Integer, nullable=False),
    Column("content_type", String(255), nullable=True),
    Column("file_size_kb", Numeric, nullable=True),
    Column("ai_score", Float, nullable=True),
    Column("timestamp", DateTime, nullable=False),
)


@dataclass
class AcquisitionRecord:
    url: str
    file_name: Optional[str]
    depth: int
    content_type: Optional[str]
    file_size_kb: Optional[float]
    ai_score: Optional[float]
    timestamp: datetime


def _resolve_db_url() -> str:
    settings = load_settings()
    if settings.db_url:
        return settings.db_url
    db_path = Path("acquisition.db").resolve()
    return f"sqlite+pysqlite:///{db_path}"


def get_engine(echo: bool = False) -> Engine:
    url = _resolve_db_url()
    engine = create_engine(url, echo=echo, future=True)
    return engine


def init_db(engine: Optional[Engine] = None) -> None:
    engine = engine or get_engine()
    metadata.create_all(engine)


@contextmanager
def session_scope(engine: Optional[Engine] = None) -> Iterator["Session"]:
    engine = engine or get_engine()
    Session = sessionmaker(bind=engine, future=True)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def insert_metadata(record: AcquisitionRecord, engine: Optional[Engine] = None) -> None:
    engine = engine or get_engine()
    values = asdict(record)
    with engine.begin() as conn:
        conn.execute(insert(acquisition_metadata).values(**values))


def get_latest_records(limit: int = 50, engine: Optional[Engine] = None) -> List[Dict[str, Any]]:
    engine = engine or get_engine()
    stmt = (
        select(
            acquisition_metadata.c.run_id,
            acquisition_metadata.c.url,
            acquisition_metadata.c.file_name,
            acquisition_metadata.c.depth,
            acquisition_metadata.c.content_type,
            acquisition_metadata.c.file_size_kb,
            acquisition_metadata.c.ai_score,
            acquisition_metadata.c.timestamp,
        )
        .order_by(acquisition_metadata.c.timestamp.desc())
        .limit(limit)
    )
    with engine.connect() as conn:
        rows = conn.execute(stmt).mappings().all()
        return [dict(r) for r in rows]


def clear_all_records(engine: Optional[Engine] = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(delete(acquisition_metadata))
