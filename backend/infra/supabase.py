"""Supabase service-role client and async connection pool (Backend v2.1 §10).

This module is the only place that constructs Supabase-specific clients and
connections:

* :func:`get_service_client` — the process-wide **service-role** ``Client``
  singleton (created by :func:`create_service_client`). Service-role access
  bypasses RLS, exactly as the repository layer requires.
* :func:`get_service_pool` — the process-wide ``asyncpg`` pool used by every
  repository. It connects with the service-role database role (the ``postgres``
  superuser), which bypasses RLS like the service-role client, and it provides
  genuine async I/O with full SQL control (explicit column lists, grouped
  aggregation, natural-key upserts, transactions).

The synchronous ``supabase`` REST client cannot express several repository
operations (grouped aggregation, natural-key upsert counts, transactional batch
activation) and is blocking; the asyncpg pool is therefore the repository layer's
data-access mechanism while the service-role ``Client`` remains available for the
REST/identity surface (later phases).

Configuration is read from the environment (``.env`` files are loaded
best-effort):

* ``SUPABASE_URL`` (fallback ``NEXT_PUBLIC_SUPABASE_URL``)
* ``SUPABASE_SERVICE_KEY`` (fallback ``SUPABASE_SERVICE_ROLE_KEY``)
* ``DATABASE_URL`` (fallback ``SUPABASE_DB_URL``)
"""
from __future__ import annotations

import os
from typing import Optional

import asyncpg
from dotenv import load_dotenv
from supabase import Client, create_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_loaded = False


def _ensure_env() -> None:
    """Load ``.env`` files once; explicit environment always wins."""
    global _loaded
    if _loaded:
        return
    load_dotenv()
    load_dotenv(override=False)
    _loaded = True


def get_supabase_url() -> str:
    """Return the configured Supabase REST base URL."""
    _ensure_env()
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL") or ""
    return url.strip()


def get_service_role_key() -> str:
    """Return the service-role (RLS-bypassing) API key."""
    _ensure_env()
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or ""
    )
    return key.strip()


def get_database_url() -> str:
    """Return the service-role Postgres connection string."""
    _ensure_env()
    url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or ""
    return url.strip().strip('"').strip("'")


# ---------------------------------------------------------------------------
# Service-role client singleton
# ---------------------------------------------------------------------------

_client: Optional[Client] = None


def create_service_client() -> Client:
    """Create a fresh Supabase service-role client (does not cache).

    Raises:
        RuntimeError: When ``SUPABASE_URL`` or the service-role key is unset.
    """
    url = get_supabase_url()
    key = get_service_role_key()
    if not url:
        raise RuntimeError(
            "SUPABASE_URL is not configured; set SUPABASE_URL or "
            "NEXT_PUBLIC_SUPABASE_URL in the environment"
        )
    if not key:
        raise RuntimeError(
            "Supabase service-role key is not configured; set "
            "SUPABASE_SERVICE_KEY or SUPABASE_SERVICE_ROLE_KEY"
        )
    return create_client(url, key)


def get_service_client() -> Client:
    """Return the process-wide service-role client (singleton)."""
    global _client
    if _client is None:
        _client = create_service_client()
    return _client


def reset_service_client() -> None:
    """Drop the cached client (used by test suites)."""
    global _client
    _client = None


# ---------------------------------------------------------------------------
# Async pool singleton
# ---------------------------------------------------------------------------

_pool: Optional[asyncpg.Pool] = None


async def get_service_pool() -> asyncpg.Pool:
    """Return the process-wide asyncpg pool (singleton, service-role role)."""
    global _pool
    if _pool is None:
        dsn = get_database_url()
        if not dsn:
            raise RuntimeError(
                "DATABASE_URL is not configured; set DATABASE_URL or "
                "SUPABASE_DB_URL in the environment"
            )
        _pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=5)
    return _pool


def close_service_pool() -> None:
    """Close and drop the cached pool (used by test suites and shutdown)."""
    global _pool
    if _pool is not None:
        _pool.terminate()
        _pool = None
