from datetime import datetime, timezone
from uuid import UUID

from domain.models.session import Session
from domain.ports.session_repository import SessionRepository

from adapters.postgres.connection import PostgresConnectionPool


class PostgresSessionRepository(SessionRepository):
    """PostgreSQL implementation of SessionRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, session: Session) -> Session:
        """Persist a new session."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sessions (id, created_at, last_accessed_at)
                VALUES (%s, %s, %s)
                RETURNING id, created_at, last_accessed_at
                """,
                (session.id, session.created_at, session.last_accessed_at),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create session")

        return Session(
            id=row[0],
            created_at=row[1],
            last_accessed_at=row[2],
        )

    def get_by_id(self, id: UUID) -> Session | None:
        """Retrieve a session by its ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, created_at, last_accessed_at
                FROM sessions
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return Session(
            id=row[0],
            created_at=row[1],
            last_accessed_at=row[2],
        )

    def update_last_accessed(self, id: UUID) -> None:
        """Update the last_accessed_at timestamp for a session."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                UPDATE sessions
                SET last_accessed_at = %s
                WHERE id = %s
                """,
                (datetime.now(timezone.utc), id),
            )
