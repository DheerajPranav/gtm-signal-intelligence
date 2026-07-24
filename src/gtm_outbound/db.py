"""Database setup: SQLite (dev) + Postgres (prod).

For v2 memory:
- Semantic memory: structured account facts (Postgres)
- Episodic memory: vector embeddings (Chroma)
- Procedural memory: playbook rules (Postgres)
"""

import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool


def get_engine():
    """Get database engine (SQLite for dev, Postgres for prod)."""
    db_url = os.getenv("DATABASE_URL")

    if db_url:
        # Production: Postgres
        engine = create_engine(
            db_url,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
        )
    else:
        # Development: SQLite
        engine = create_engine(
            "sqlite:///gtm_outbound.db",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
        )

    return engine


def init_db():
    """Create tables from SQLModel definitions."""
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    return engine


def get_session():
    """Get a database session."""
    engine = get_engine()
    return Session(engine)
