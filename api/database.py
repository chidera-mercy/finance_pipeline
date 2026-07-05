"""
Database connection pooling for the API layer.
"""
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2

load_dotenv()


_pool: psycopg2.pool.SimpleConnectionPool | None = None

def init_pool(minconn: int = 1, maxconn: int = 10) -> None:
    """Create the global connection pool. Call once on app startup."""
    global _pool
    if _pool is not None:
        return
    
    _pool = psycopg2.pool.SimpleConnectionPool(
        minconn,
        maxconn,
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

def close_pool() -> None:
    """Close all pooled connections. Call on app shutdown."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None

@contextmanager
def get_connection():
    """
    Checks a connection out of the pool and returns it.
    """
    if _pool is None:
        raise RuntimeError("Connection pool is not initialised. Call init_pool() first.")
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)

def get_db():
    """
    FastAPI dependency. Yields a live connection for the duration of
    a single request. Tests override this dependency to inject a
    mock connection instead of hitting a real database.
    """
    with get_connection() as conn:
        yield conn
