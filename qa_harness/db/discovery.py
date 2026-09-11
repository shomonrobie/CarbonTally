"""Read-only resource discovery for API/workflow probes (V1.2).

Resource-bound probes (receive a message, open another org's conversation)
are meaningless against a fake all-zero id — a 404 then proves nothing. This
module finds REAL ids with parameterized SELECT-only queries so those probes
either run against a real resource or SKIP with an explicit reason.

Safety rules (spec §33):

* Every query is a SELECT; no writes are ever issued.
* Missing tables/columns return ``None`` instead of raising, so DB QA
  degradation never breaks API/workflow QA.
* Results are cached per process; connections are closed on :meth:`close`.
* No credentials, tokens or query results are ever logged.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

try:
    import psycopg2  # type: ignore
    _PSYCOPG2 = True
except ImportError:  # pragma: no cover
    psycopg2 = None  # type: ignore
    _PSYCOPG2 = False

_CONVERSATION_BY_PARTICIPANT = """
    SELECT c.id
    FROM conversations c
    JOIN conversation_participants p ON p.conversation_id = c.id
    JOIN users u ON u.id = p.user_id
    WHERE u.email = %s
    ORDER BY c.last_message_at DESC NULLS LAST
    LIMIT 1
"""

_CONVERSATION_BY_ORG = """
    SELECT id FROM conversations
    WHERE organization_id = %s
    ORDER BY last_message_at DESC NULLS LAST
    LIMIT 1
"""

_CONVERSATION_OTHER_ORG = """
    SELECT id FROM conversations
    WHERE organization_id IS DISTINCT FROM %s
    ORDER BY last_message_at DESC NULLS LAST
    LIMIT 1
"""


class ResourceDiscovery:
    """Lazily connected, read-only resource lookups against the QA database.

    All lookups degrade to ``None`` on any error (missing table, bad schema,
    unreachable DB) — callers treat ``None`` as "cannot verify, skip".
    """

    def __init__(self, dsn: str, *, connect_timeout: int = 5) -> None:
        self._dsn = dsn
        self._connect_timeout = connect_timeout
        self._conn: Any = None
        self._cache: Dict[Tuple[str, str], Optional[str]] = {}

    # ------------------------------------------------------------------ #

    def _scalar(self, sql: str, params: Tuple[Any, ...],
                key: Tuple[str, str]) -> Optional[str]:
        if key in self._cache:
            return self._cache[key]
        value: Optional[str] = None
        try:
            conn = self._connect()
            cur = conn.cursor()
            try:
                cur.execute(sql, params)
                row = cur.fetchone()
                value = str(row[0]) if row and row[0] is not None else None
            finally:
                cur.close()
        except Exception:
            value = None
        self._cache[key] = value
        return value

    def _connect(self) -> Any:
        if _PSYCOPG2 is False:
            raise RuntimeError("psycopg2 unavailable")
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self._dsn,
                                          connect_timeout=self._connect_timeout)
        return self._conn

    # ------------------------------------------------------------------ #

    def conversation_id_for(self, email: str) -> Optional[str]:
        """Most recent conversation the given user participates in."""
        return self._scalar(_CONVERSATION_BY_PARTICIPANT, (email,),
                            ("conv_email", email))

    def conversation_id_for_org(self, organization_id: str) -> Optional[str]:
        """Most recent conversation scoped to the given organisation."""
        return self._scalar(_CONVERSATION_BY_ORG, (organization_id,),
                            ("conv_org", organization_id))

    def conversation_id_for_other_org(self, organization_id: str) -> Optional[str]:
        """Most recent conversation that is NOT scoped to the given org."""
        return self._scalar(_CONVERSATION_OTHER_ORG, (organization_id,),
                            ("conv_other", organization_id))

    # ------------------------------------------------------------------ #

    def item_id_in_stage(self, organization_id: str, stage: str) -> Optional[str]:
        """A workflow item in the given stage for the org (future mutation
        scope use). Returns None if the table/schema is absent."""
        sql = """
            SELECT id FROM manual_extraction_items
            WHERE organization_id = %s AND stage = %s
            ORDER BY updated_at DESC NULLS LAST
            LIMIT 1
        """
        return self._scalar(sql, (organization_id, stage),
                            ("item_stage", f"{organization_id}:{stage}"))

    def close(self) -> None:
        if self._conn is not None and not self._conn.closed:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = None

    def __enter__(self) -> "ResourceDiscovery":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
