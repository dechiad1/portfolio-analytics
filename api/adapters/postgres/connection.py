from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg_pool import ConnectionPool


class PostgresConnectionPool:
    """Manages PostgreSQL connection pooling."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_size: int = 2,
        max_size: int = 10,
    ) -> None:
        conninfo = (
            f"host={host} port={port} dbname={database} user={user} password={password}"
        )
        self._pool = ConnectionPool(
            conninfo=conninfo,
            min_size=min_size,
            max_size=max_size,
            open=True,
        )

    @contextmanager
    def connection(self) -> Generator[psycopg.Connection, None, None]:
        """Get a connection from the pool."""
        with self._pool.connection() as conn:
            yield conn

    @contextmanager
    def cursor(self) -> Generator[psycopg.Cursor, None, None]:
        """Get a cursor from a pooled connection."""
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                yield cur
                conn.commit()

    @contextmanager
    def transaction(self) -> Generator[psycopg.Cursor, None, None]:
        """Get a cursor within a transaction. Commits on success, rolls back on exception."""
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                try:
                    yield cur
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

    def close(self) -> None:
        """Close the connection pool."""
        self._pool.close()
