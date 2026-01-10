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

    def close(self) -> None:
        """Close the connection pool."""
        self._pool.close()

    def initialize_schema(self) -> None:
        """Create required database tables if they don't exist."""
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id UUID PRIMARY KEY,
                        created_at TIMESTAMPTZ NOT NULL,
                        last_accessed_at TIMESTAMPTZ NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS holdings (
                        id UUID PRIMARY KEY,
                        session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                        ticker VARCHAR(20) NOT NULL,
                        name VARCHAR(255) NOT NULL,
                        asset_class VARCHAR(100) NOT NULL,
                        sector VARCHAR(100) NOT NULL,
                        broker VARCHAR(100) NOT NULL,
                        purchase_date DATE NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_holdings_session_id
                    ON holdings(session_id)
                """)
            conn.commit()
