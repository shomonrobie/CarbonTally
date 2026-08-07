"""CarbonTally infrastructure package (Backend v2.1 §10, §19).

Holds all external-service integration (Supabase service-role client and the
async Postgres connection pool). Nothing in this package imports from the
``domain`` package; repositories bridge the two.
"""
