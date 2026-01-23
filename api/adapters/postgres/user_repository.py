from datetime import datetime
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
                INSERT INTO users (id, email, password_hash, created_at, is_admin,
                                   last_login, oauth_provider, oauth_subject)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, email, password_hash, created_at, is_admin,
                          last_login, oauth_provider, oauth_subject
                """,
                (
                    user.id,
                    user.email,
                    user.password_hash,
                    user.created_at,
                    user.is_admin,
                    user.last_login,
                    user.oauth_provider,
                    user.oauth_subject,
                ),
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
                SELECT id, email, password_hash, created_at, is_admin,
                       last_login, oauth_provider, oauth_subject
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
                SELECT id, email, password_hash, created_at, is_admin,
                       last_login, oauth_provider, oauth_subject
                FROM users
                WHERE email = %s
                """,
                (email.lower(),),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_user(row)

    def get_by_oauth_subject(self, provider: str, subject: str) -> User | None:
        """Retrieve a user by OAuth provider and subject."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                SELECT id, email, password_hash, created_at, is_admin,
                       last_login, oauth_provider, oauth_subject
                FROM users
                WHERE oauth_provider = %s AND oauth_subject = %s
                """,
                (provider, subject),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_user(row)

    def update_last_login(self, user_id: UUID, last_login: datetime) -> None:
        """Update the user's last login timestamp."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET last_login = %s
                WHERE id = %s
                """,
                (last_login, user_id),
            )

    def set_admin(self, user_id: UUID, is_admin: bool) -> None:
        """Update the user's admin status."""
        with self._pool.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET is_admin = %s
                WHERE id = %s
                """,
                (is_admin, user_id),
            )

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
            is_admin=row[4] if len(row) > 4 else False,
            last_login=row[5] if len(row) > 5 else None,
            oauth_provider=row[6] if len(row) > 6 else None,
            oauth_subject=row[7] if len(row) > 7 else None,
        )
