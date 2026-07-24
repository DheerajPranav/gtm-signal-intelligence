"""Database setup: SQLite (dev) + Postgres (prod).

v2 memory storage splits by access pattern:
  - semantic + procedural memory -> SQL (point lookups, aggregation, supersession)
  - episodic embeddings          -> Chroma (similarity search)
  - episodic *metadata*          -> SQL, so consolidation can GROUP BY segment
"""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

DEFAULT_SQLITE_URL = "sqlite:///gtm_outbound.db"


def get_engine(url: Optional[str] = None, echo: Optional[bool] = None):
    """Engine for the configured database. Postgres when DATABASE_URL is set."""
    resolved = url or os.getenv("DATABASE_URL") or DEFAULT_SQLITE_URL
    verbose = echo if echo is not None else os.getenv("SQL_DEBUG", "false").lower() == "true"

    if resolved.startswith("sqlite"):
        return create_engine(
            resolved,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=verbose,
        )
    return create_engine(resolved, echo=verbose)


def init_db(url: Optional[str] = None, engine=None):
    """Create every table and verify at least one exists.

    The import below is load-bearing: SQLModel only registers a table on
    `SQLModel.metadata` when its module is imported. Without it `create_all()`
    succeeds against an empty metadata and creates nothing — which is exactly
    how this silently shipped creating zero tables.
    """
    from . import tables  # noqa: F401  — registers tables on SQLModel.metadata

    engine = engine or get_engine(url)
    SQLModel.metadata.create_all(engine)

    if not SQLModel.metadata.tables:
        raise RuntimeError(
            "init_db() created no tables — SQLModel table classes were never "
            "registered. Check that gtm_outbound.tables is importable."
        )
    return engine


def get_session(engine=None) -> Session:
    return Session(engine or get_engine())
