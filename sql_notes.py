import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, insert, select


class SQLNoteStore:
    """Minimal SQL-backed note storage for the gallery page."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL is required")

        self.engine = create_engine(self.database_url)
        self.metadata = MetaData()
        self.notes = Table(
            "notes",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("content", String(2000), nullable=False),
            Column("created_at", DateTime, nullable=False, default=datetime.utcnow),
        )
        self.metadata.create_all(self.engine)

    def add_note(self, content: str) -> None:
        normalized = content.strip()
        if not normalized:
            return

        with self.engine.begin() as connection:
            connection.execute(
                insert(self.notes).values(content=normalized, created_at=datetime.utcnow())
            )

    def list_notes(self, limit: int = 25) -> list[dict[str, str]]:
        stmt = (
            select(self.notes.c.content, self.notes.c.created_at)
            .order_by(self.notes.c.created_at.desc(), self.notes.c.id.desc())
            .limit(limit)
        )
        with self.engine.connect() as connection:
            rows = connection.execute(stmt).all()

        return [
            {
                "content": row.content,
                "created_at": row.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for row in rows
        ]