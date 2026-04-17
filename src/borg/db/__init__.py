"""Borg database connection pool + migration runner."""

import os
from contextlib import asynccontextmanager

import asyncpg
import structlog

from borg.config import settings

log = structlog.get_logger()

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        dsn = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_conn():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def run_migrations():
    """Run SQL migration files on startup.

    Idempotent — the migrations use CREATE TABLE IF NOT EXISTS,
    CREATE INDEX IF NOT EXISTS, CREATE OR REPLACE FUNCTION,
    INSERT ... ON CONFLICT, and ALTER TABLE ... IF NOT EXISTS.
    Safe to run every time the engine starts.

    Uses a raw psycopg-style connection to execute full SQL scripts
    (asyncpg's execute() handles multi-statement SQL fine).
    """
    # Look for migrations/ in the working directory (Docker: /app/migrations/)
    migrations_dir = os.path.join(os.getcwd(), "migrations")
    if not os.path.isdir(migrations_dir):
        # Fallback: relative to the package source
        pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        migrations_dir = os.path.join(pkg_dir, "migrations")

    if not os.path.isdir(migrations_dir):
        log.warning("migrations.dir_not_found", searched=migrations_dir)
        return

    sql_files = sorted(f for f in os.listdir(migrations_dir) if f.endswith(".sql"))
    if not sql_files:
        log.info("migrations.no_files")
        return

    pool = await get_pool()
    async with pool.acquire() as conn:
        for filename in sql_files:
            filepath = os.path.join(migrations_dir, filename)
            sql = open(filepath, "r").read()

            try:
                # asyncpg execute() supports multi-statement SQL
                await conn.execute(sql)
                log.info("migrations.applied", file=filename)
            except asyncpg.exceptions.DuplicateTableError:
                log.info("migrations.skipped", file=filename, reason="tables_exist")
            except asyncpg.exceptions.DuplicateObjectError:
                log.info("migrations.skipped", file=filename, reason="objects_exist")
            except asyncpg.exceptions.UniqueViolationError:
                log.info("migrations.skipped", file=filename, reason="data_exists")
            except Exception as e:
                log.error("migrations.error", file=filename, error=str(e))
                # Don't crash — log and continue with next file
