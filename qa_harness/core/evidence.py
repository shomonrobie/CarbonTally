"""Evidence path management.

Every artifact (screenshot, trace, video, API response, DB snapshot, console
log, network log) is stored under ``qa_harness/evidence/<kind>/`` with a
deterministic, sanitized filename. A capture is only meaningful when the page
is ready — the browser layer enforces readiness conditions *before* calling
:meth:`EvidenceStore.path` (spec §26).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

KINDS = ("screenshots", "traces", "videos", "api", "db", "console", "network")

_UNSAFE = re.compile(r"[^A-Za-z0-9_.\-]+")


def sanitize_token(token: str, fallback: str = "unnamed") -> str:
    """Make a free-text token (role/route/persona) safe for a filename."""
    cleaned = _UNSAFE.sub("_", token).strip("_")
    return cleaned[:80] or fallback


class EvidenceStore:
    """Resolves and creates evidence paths under the evidence/ tree."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent / "evidence"
        for kind in KINDS:
            (self.base_dir / kind).mkdir(parents=True, exist_ok=True)

    def path(self, kind: str, run_id: str, role: str, name: str,
             route: str = "", ext: str = "json") -> Path:
        """Return the path for a new evidence artifact.

        ``run_id`` is typically ``20260824T150000_<shortsha>``; ``role`` and
        ``route`` are sanitized; collisions are avoided with a UTC timestamp
        suffix only when the target already exists (never overwrite).
        """
        if kind not in KINDS:
            raise ValueError(f"Unknown evidence kind {kind!r}; expected one of {KINDS}")
        directory = self.base_dir / kind
        stem = "_".join(
            part
            for part in (
                sanitize_token(run_id),
                sanitize_token(role),
                sanitize_token(route),
                sanitize_token(name),
            )
            if part
        )
        candidate = directory / f"{stem}.{ext.lstrip('.')}"
        if candidate.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            candidate = directory / f"{stem}_{stamp}.{ext.lstrip('.')}"
        return candidate

    def write(self, kind: str, run_id: str, role: str, name: str, content: str,
              route: str = "", ext: str = "json") -> Path:
        """Write text content to an evidence path and return the path."""
        path = self.path(kind, run_id, role, name, route=route, ext=ext)
        path.write_text(content, encoding="utf-8")
        return path
