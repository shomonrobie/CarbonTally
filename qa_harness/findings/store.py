"""Finding persistence across the three stages (spec §28, §30).

* raw/          — every finding exactly as produced (JSON lines)
* normalized/   — normalized + assigned QA-<CAT>-NNN ids
* deduplicated/ — canonical findings after deduplication

Stored JSON is redacted by the caller (the store itself stores raw dicts; the
report layer redacts on output).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from qa_harness.core.findings import Finding

FINDINGS_BASE = Path(__file__).resolve().parent


def stage_dir(name: str) -> Path:
    path = FINDINGS_BASE / name
    path.mkdir(parents=True, exist_ok=True)
    return path


class FindingStore:
    """Persists findings to raw/normalized/deduplicated JSON files."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else FINDINGS_BASE
        self.raw_dir = self.base_dir / "raw"
        self.normalized_dir = self.base_dir / "normalized"
        self.dedup_dir = self.base_dir / "deduplicated"
        for directory in (self.raw_dir, self.normalized_dir, self.dedup_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def _dump(self, directory: Path, filename: str, items: Iterable[Dict[str, Any]]) -> Path:
        path = directory / filename
        with path.open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
        return path

    def save_raw(self, findings: Iterable[Finding], filename: str = "raw.jsonl") -> Path:
        return self._dump(self.raw_dir, filename, (f.to_dict() for f in findings))

    def save_normalized(self, findings: Iterable[Finding], filename: str = "normalized.jsonl") -> Path:
        return self._dump(self.normalized_dir, filename, (f.to_dict() for f in findings))

    def save_deduplicated(self, findings: Iterable[Finding], filename: str = "deduplicated.jsonl") -> Path:
        return self._dump(self.dedup_dir, filename, (f.to_dict() for f in findings))

    def load_jsonl(self, directory: str, filename: str) -> List[Finding]:
        path = Path(self.base_dir) / directory / filename
        if not path.exists():
            return []
        result = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    result.append(Finding.from_dict(json.loads(line)))
        return result
