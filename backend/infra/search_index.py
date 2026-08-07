"""In-memory factor search index (Backend v2.1 §16, CT-ARCH-011).

Implements :class:`domain.matching.FactorSearch` — the retrieval contract the
matching stages use. The index is a process singleton loaded at startup from
the repository and rebuilt after an import is published. It holds:

* a natural-key map for exact lookups, and
* a token inverted index over ``activity_type`` for keyword retrieval.

:meth:`keyword_search` scores candidates by query-token coverage, which makes
the index a deterministic first retrieval stage for the matching pipeline while
staying free of any matching *decisions* (those live in the engines, Phase 4).

Dependency rules: this module imports only from ``core`` (none needed), the
``domain`` package (factor types) and the repository layer (the loader). No
business logic lives here.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable, Optional, Protocol

from domain.factor import EmissionFactor

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> tuple[str, ...]:
    """Return the lower-case alphanumeric tokens of ``text``.

    ``"Diesel (kg CO2e) [litres]"`` becomes ``("diesel", "kg", "co2e", "litres")``.
    """
    return tuple(_TOKEN_RE.findall(text.casefold()))


class FactorSource(Protocol):
    """Anything that can supply the full factor set for the index (the
    ``EmissionFactorsRepository`` satisfies this)."""

    async def load_all_for_index(self) -> list[EmissionFactor]: ...


class FactorSearchIndex:
    """An in-memory factor index that is rebuilt in place on import events.

    Args:
        default_limit: Result limit used by :meth:`keyword_search` when the
            caller does not supply one.
    """

    def __init__(self, default_limit: int = 10) -> None:
        if default_limit < 1:
            raise ValueError("default_limit must be >= 1")
        self._default_limit = default_limit
        self._factors: list[EmissionFactor] = []
        self._by_id: dict[str, EmissionFactor] = {}
        self._by_natural_key: dict[tuple[str, ...], EmissionFactor] = {}
        self._tokens_by_index: dict[int, tuple[str, ...]] = {}
        self._inverted: dict[str, set[int]] = defaultdict(set)

    @property
    def default_limit(self) -> int:
        """The configured default result limit."""
        return self._default_limit

    # ------------------------------------------------------------------
    # Loading / mutation
    # ------------------------------------------------------------------

    def load(self, factors: Iterable[EmissionFactor]) -> None:
        """Replace the index contents with ``factors``."""
        self._factors = []
        self._by_id = {}
        self._by_natural_key = {}
        self._tokens_by_index = {}
        self._inverted = defaultdict(set)
        self.add_many(factors)

    def rebuild(self, factors: Iterable[EmissionFactor]) -> None:
        """Alias of :meth:`load` — the post-import refresh path."""
        self.load(factors)

    def add_many(self, factors: Iterable[EmissionFactor]) -> None:
        """Add ``factors``, replacing any existing factor with the same id."""
        for factor in factors:
            self.add(factor)

    def add(self, factor: EmissionFactor) -> None:
        """Add one factor, replacing an existing factor with the same id."""
        if factor.id in self._by_id:
            self.remove(factor.id)
        index = len(self._factors)
        self._factors.append(factor)
        self._by_id[factor.id] = factor
        if factor.natural_key:
            self._by_natural_key[factor.natural_key] = factor
        tokens = _tokens(factor.activity_type)
        self._tokens_by_index[index] = tokens
        for token in set(tokens):
            self._inverted[token].add(index)

    def remove(self, factor_id: str) -> bool:
        """Remove the factor with ``factor_id``; return ``True`` when found."""
        factor = self._by_id.get(factor_id)
        if factor is None:
            return False
        self._factors = [f for f in self._factors if f.id != factor_id]
        self._by_id.pop(factor_id)
        if (
            factor.natural_key
            and self._by_natural_key.get(factor.natural_key) is factor
        ):
            self._by_natural_key.pop(factor.natural_key)
        self._rebuild_token_tables()
        return True

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get(self, factor_id: str) -> Optional[EmissionFactor]:
        """Return the factor with ``factor_id``, or ``None``."""
        return self._by_id.get(factor_id)

    def exact_natural_key(
        self, key: tuple[str, ...]
    ) -> Optional[EmissionFactor]:
        """Return the factor matching the exact RC2 natural key, or ``None``."""
        return self._by_natural_key.get(key)

    def keyword_search(
        self,
        query: str,
        unit: Optional[str] = None,
        country: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 10,
    ) -> list[tuple[EmissionFactor, float]]:
        """Return up to ``limit`` factors ranked by query-token coverage.

        The score is the fraction of query tokens present in the factor's
        ``activity_type`` tokens (1.0 = every token matched). Results are
        ordered deterministically: score descending, then activity type and id
        ascending. ``unit``/``country``/``provider`` narrow the candidate set.

        Raises:
            ValueError: When ``limit`` is less than 1.
        """
        if limit < 1:
            raise ValueError("limit must be >= 1")
        tokens = _tokens(query)
        if not tokens:
            return []
        token_set = frozenset(tokens)
        candidates: set[int] = set()
        for token in token_set:
            candidates.update(self._inverted.get(token, ()))
        scored: list[tuple[EmissionFactor, float]] = []
        for index in candidates:
            factor = self._factors[index]
            if unit is not None and factor.unit != unit:
                continue
            if country is not None and factor.country != country:
                continue
            if provider is not None and factor.provider_key != provider:
                continue
            overlap = len(token_set & set(self._tokens_by_index[index]))
            scored.append((factor, overlap / len(token_set)))
        scored.sort(
            key=lambda pair: (
                -pair[1],
                pair[0].activity_type.casefold(),
                pair[0].id,
            )
        )
        return scored[:limit]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._factors)

    def snapshot(self) -> tuple[EmissionFactor, ...]:
        """Return the indexed factors in insertion order."""
        return tuple(self._factors)

    @classmethod
    async def from_repository(
        cls,
        repository: FactorSource,
        *,
        default_limit: int = 10,
    ) -> "FactorSearchIndex":
        """Build an index from a repository's full factor set."""
        index = cls(default_limit=default_limit)
        index.load(await repository.load_all_for_index())
        return index

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _rebuild_token_tables(self) -> None:
        self._tokens_by_index = {}
        self._inverted = defaultdict(set)
        for index, factor in enumerate(self._factors):
            tokens = _tokens(factor.activity_type)
            self._tokens_by_index[index] = tokens
            for token in set(tokens):
                self._inverted[token].add(index)


_index: Optional[FactorSearchIndex] = None


def get_search_index() -> FactorSearchIndex:
    """Return the process-wide search index (singleton, empty until loaded)."""
    global _index
    if _index is None:
        _index = FactorSearchIndex()
    return _index


def reset_search_index() -> None:
    """Drop the cached index (used by test suites)."""
    global _index
    _index = None

