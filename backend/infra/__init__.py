"""CarbonTally infrastructure package (Backend v2.1 §10, §14–§19).

Holds the external-service integrations (Supabase service-role client and the
async Postgres connection pool in ``supabase``) and the platform infrastructure
components (``config``, ``event_bus``, ``search_index``, ``audit_logger``).

Layer rules (Backend v2.1 §5): infrastructure may import from ``core`` and
``domain``, and it may use the repository layer — it must never contain
business logic. Engines (Phase 4+) depend on this package, never the reverse.
"""

