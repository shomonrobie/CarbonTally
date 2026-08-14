"""Uvicorn entry point for the CarbonTally Backend v2.1 API (Phase 10).

Run::

    uvicorn main_v2:app --reload --port 8001

The legacy ``main.py`` application is untouched; the v2.1 API is served here so
the two surfaces can coexist during the migration (prep-pack §5: ``main.py`` is
the app factory — this module provides that factory under a non-conflicting
name because ``main.py`` is occupied by the legacy app).
"""
from __future__ import annotations

from api.router import create_app

app = create_app()

__all__ = ["app"]
