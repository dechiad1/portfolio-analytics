from uuid import UUID

from domain.models.user import User
from domain.ports.user_repository import UserRepository

from adapters.postgres.connection import PostgresConnectionPool


class PostgresUserRepository(UserRepository):
    """PostgreSQL implementation of UserRepository."""

    def __init__(self, pool: PostgresConnectionPool) -> None:
        self._pool = pool

    def create(self, user: User) -> User:
        """Persist a new user."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id, email, password_hash, created_at
                """,
                (user.id, user.email, user.password_hash, user.created_at),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create user")

        return self._row_to_user(row)

    def get_by_id(self, id: UUID) -> User | None:
        """Retrieve a user by ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, password_hash, created_at
                FROM users
                WHERE id = %s
                """,
                (id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_user(row)

    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, password_hash, created_at
                FROM users
                WHERE email = %s
                """,
                (email.lower(),),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_user(row)

    def delete(self, id: UUID) -> None:
        """Delete a user by ID."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                DELETE FROM users
                WHERE id = %s
                """,
                (id,),
            )

    def _row_to_user(self, row: tuple) -> User:
        """Convert a database row to a User model."""
        return User(
            id=row[0],
            email=row[1],
            password_hash=row[2],
            created_at=row[3],
        )
