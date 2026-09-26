"""P17-M2 — the governed capability catalogue's own identity (`DEF-1` regression).

`P17-M` (independent verification) falsified one `P17-L` claim: the capability
truth surface could be hijacked. The read surface selected the **first** framework
version that carried *at least one* governed requirement code, ordered by
``status = 'IN_FORCE'``, then ``source_tier``, then ``version_label``. A competing
version that was ``IN_FORCE``, ``source_tier`` 1, sorted lexically earlier and
carried a single governed code (``GP-S3-CAT-01`` → ``SUPPORTED``) therefore
replaced the governed catalogue and published a **narrower, upgraded** claim
(1 requirement, rollup ``1/0/0/0`` instead of ``4/6/3/2``).

`P17-M2` makes the selection *identity-anchored*: a candidate is the governed
catalogue only if **every** one of its requirement rows is a governed requirement
identity **and** it carries the **complete** governed identity set. A candidate's
position in the list is never consulted, so no ``ORDER BY`` can decide a product
claim.

This module pins the rule itself, in process, with no database:

* the identity set is the complete governed catalogue (18 identities);
* selection is position-independent — `DEF-1`'s exact adversarial candidate is
  offered *first*, in `DEF-1`'s order, and still loses;
* a subset, a superset carrying a non-governed row, an empty set and an
  all-ungoverned set are never the catalogue;
* a **duplicate** complete governed identity is refused (fail closed), because an
  ambiguous catalogue is a governance fault (a PO decision), not a tie-break;
* the selector mutates nothing, adds no field, and declares no vocabulary.
"""
from __future__ import annotations

import inspect
from typing import Any, Optional, Sequence

import pytest

from domain import capability_catalogue as cc
from domain.disclosure import CARBONTALLY_CAPABILITIES, DisclosureViolation

#: The persisted identity of the governed catalogue version (`P17-K`).
GOVERNED_VERSION_ID = "22222222-2222-4222-8222-222222222222"
GOVERNED_LABEL = "Corporate Accounting and Reporting Standard (2004 revised edition)"

#: The frozen `M-1` image of the Scope 3 category matrix (P17-DECISION-03
#: §11.1/§11.2). The non-upgrading invariant is asserted against exactly this map.
M1_IMAGE: dict[str, str] = {
    "GP-S3-CAT-01": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-02": "MISSING_CAPABILITY",
    "GP-S3-CAT-03": "SUPPORTED",
    "GP-S3-CAT-04": "SUPPORTED",
    "GP-S3-CAT-05": "SUPPORTED",
    "GP-S3-CAT-06": "SUPPORTED",
    "GP-S3-CAT-07": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-08": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-09": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-10": "MISSING_CAPABILITY",
    "GP-S3-CAT-11": "FUTURE",
    "GP-S3-CAT-12": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-13": "PARTIALLY_SUPPORTED",
    "GP-S3-CAT-14": "FUTURE",
    "GP-S3-CAT-15": "FUTURE",
}

#: The four-way rollup (`S3-1`) — reported in full, never as a total.
ROLLUP: dict[str, int] = {
    "SUPPORTED": 4,
    "PARTIALLY_SUPPORTED": 6,
    "FUTURE": 3,
    "MISSING_CAPABILITY": 2,
}

#: The codes the governed catalogue persists, in catalogue order.
GOVERNED_CODES: tuple[str, ...] = ("GP-S1", "GP-S2-LB", "GP-S2-MB", *tuple(M1_IMAGE))


def _candidate(
    *,
    version_id: str,
    label: str,
    codes: Sequence[str],
    status: str = "IN_FORCE",
    source_tier: int = 1,
) -> dict[str, Any]:
    """One candidate framework version in the shape the repository returns."""
    return {
        "id": version_id,
        "framework_id": "11111111-1111-4111-8111-111111111111",
        "version_label": label,
        "legal_reference": None,
        "source_tier": source_tier,
        "source_url": "https://ghgprotocol.org/corporate-standard",
        "authoritative_source_date": None,
        "status": status,
        "applicable_from": None,
        "applicable_to": None,
        "verified_at": None,
        "framework_code": "GHG_PROTOCOL",
        "requirement_codes": list(codes),
    }


def _governed(**kw: Any) -> dict[str, Any]:
    """The governed catalogue version (complete identity set by default)."""
    kw.setdefault("version_id", GOVERNED_VERSION_ID)
    kw.setdefault("label", GOVERNED_LABEL)
    kw.setdefault("codes", GOVERNED_CODES)
    return _candidate(**kw)


def _def1_adversary(suffix: str = "AAA") -> dict[str, Any]:
    """The exact `P17-M` hijack candidate: IN_FORCE, tier 1, lexically earlier.

    It carries **one** governed requirement code — `GP-S3-CAT-01`, whose governed
    value is `PARTIALLY_SUPPORTED` and whose adversarial value is `SUPPORTED`.
    """
    return _candidate(
        version_id="33333333-3333-4333-8333-333333333333",
        label=f"{suffix}-P17M2-hijack",
        codes=["GP-S3-CAT-01"],
        status="IN_FORCE",
        source_tier=1,
    )


def _pre_fix_rule(candidates: Sequence[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """The `DEF-1` selection rule, preserved here **as evidence only**.

    This mirrors the shipped pre-fix logic (order by `IN_FORCE`, `source_tier`,
    `version_label`; take the first candidate carrying ≥1 governed code) so the
    adversarial fixtures can be shown to actually defeat it. Production code no
    longer contains this rule; a test asserts that below.
    """

    def _sort_key(candidate: dict[str, Any]) -> tuple[int, int, str]:
        return (
            0 if candidate.get("status") == "IN_FORCE" else 1,
            int(candidate.get("source_tier") or 0),
            str(candidate.get("version_label") or ""),
        )

    for candidate in sorted(candidates, key=_sort_key):
        if any(
            cc.is_governed_requirement_code(code)
            for code in (candidate.get("requirement_codes") or [])
        ):
            return candidate
    return None


# ===========================================================================
# 1. The governed identity set
# ===========================================================================
def test_the_governed_identity_set_is_the_complete_governed_catalogue() -> None:
    """Scope 1 + the two governed Scope 2 methods + the 15 Scope 3 categories."""
    identities = cc.GOVERNED_CATALOGUE_IDENTITIES
    assert len(identities) == 18, sorted(identities)
    assert identities == set(GOVERNED_CODES), sorted(identities ^ set(GOVERNED_CODES))
    assert {"GP-S1", "GP-S2-LB", "GP-S2-MB"} <= identities
    assert tuple(sorted(M1_IMAGE)) == tuple(
        f"GP-S3-CAT-{category:02d}" for category in range(1, 16)
    )


def test_the_identity_set_and_the_identity_grammar_cannot_drift() -> None:
    """Every member is a governed identity, and near-misses are not."""
    for identity in sorted(cc.GOVERNED_CATALOGUE_IDENTITIES):
        assert cc.is_governed_requirement_code(identity) is True, identity
    for near_miss in ("GP-S3-CAT-16", "GP-S3-CAT-0", "GP-S2-XX", "GP-S3", ""):
        assert near_miss not in cc.GOVERNED_CATALOGUE_IDENTITIES
        assert cc.is_governed_requirement_code(near_miss) is False, near_miss


# ===========================================================================
# 2. The defect mechanism, preserved as evidence
# ===========================================================================
def test_the_def1_adversary_really_defeats_the_pre_fix_rule() -> None:
    """`DEF-1`'s candidate set, replayed — the hijack was real.

    A competing `IN_FORCE` tier-1 version with a lexically earlier label and one
    governed code is exactly what the pre-fix rule selected. If this assertion
    ever fails, the adversarial fixtures below have stopped reproducing `DEF-1`.
    """
    adversary = _def1_adversary()
    hijacked = _pre_fix_rule([adversary, _governed()])
    assert hijacked is not None
    assert hijacked["id"] == adversary["id"]
    assert hijacked["requirement_codes"] == ["GP-S3-CAT-01"]

    # ... and the shipped rule refuses it.
    assert cc.is_governed_catalogue_version(adversary) is False
    selected = cc.select_governed_catalogue_version([adversary, _governed()])
    assert selected is not None and selected["id"] == GOVERNED_VERSION_ID


# ===========================================================================
# 3. Selection is identity-anchored, never positional
# ===========================================================================
def _two_hijacks_before() -> list[dict[str, Any]]:
    return [_def1_adversary("AAA"), _def1_adversary("AAB"), _governed()]


@pytest.mark.parametrize(
    "candidates",
    [
        pytest.param([_governed(), _def1_adversary()], id="governed-first"),
        pytest.param([_def1_adversary(), _governed()], id="hijack-first"),
        pytest.param(_two_hijacks_before(), id="two-hijacks-before"),
        pytest.param(
            [
                _candidate(
                    version_id="77777777-7777-4777-8777-777777777777",
                    label="AAA-narrower",
                    codes=["GP-S3-CAT-01"],
                ),
                _governed(),
            ],
            id="narrower-before-governed",
        ),
    ],
)
def test_selection_never_depends_on_position(candidates: list[dict[str, Any]]) -> None:
    selected = cc.select_governed_catalogue_version(candidates)
    assert selected is not None
    assert selected["id"] == GOVERNED_VERSION_ID
    assert selected["version_label"] == GOVERNED_LABEL
    assert set(selected["requirement_codes"]) == set(GOVERNED_CODES)


@pytest.mark.parametrize("status", ["IN_FORCE", "SUPERSEDED", "DRAFT", "WITHDRAWN"])
@pytest.mark.parametrize("source_tier", [1, 2, 3])
def test_selection_is_independent_of_status_tier_and_label(
    status: str, source_tier: int
) -> None:
    """`status`, `source_tier` and the label ordering carry no precedence."""
    governed = _governed(status=status, source_tier=source_tier, label="zzz-late-label")
    adversary = _def1_adversary()
    selected = cc.select_governed_catalogue_version([adversary, governed])
    assert selected is not None and selected["id"] == GOVERNED_VERSION_ID
    assert cc.is_governed_catalogue_version(adversary) is False
    assert cc.is_governed_catalogue_version(governed) is True


# ===========================================================================
# 4. What is NOT the catalogue
# ===========================================================================
def test_a_single_governed_code_never_makes_a_catalogue() -> None:
    """`DEF-1` core (`AG-7`): a one-code version is not the product catalogue."""
    for code in GOVERNED_CODES:
        candidate = _candidate(
            version_id="33333333-3333-4333-8333-333333333333",
            label="AAA-single",
            codes=[code],
        )
        assert cc.is_governed_catalogue_version(candidate) is False, code
        assert (
            cc.select_governed_catalogue_version([candidate, _governed()])["id"]
            == GOVERNED_VERSION_ID
        )


def test_a_subset_of_the_governed_identities_is_never_the_catalogue() -> None:
    """A narrower catalogue dressed as the canonical one is refused."""
    for missing in GOVERNED_CODES:
        codes = [code for code in GOVERNED_CODES if code != missing]
        candidate = _candidate(
            version_id="33333333-3333-4333-8333-333333333333",
            label="AAA-subset",
            codes=codes,
        )
        assert cc.is_governed_catalogue_version(candidate) is False, missing


def test_a_non_governed_row_disqualifies_a_complete_looking_candidate() -> None:
    """A version carrying residue is not a capability catalogue at all."""
    candidate = _candidate(
        version_id="33333333-3333-4333-8333-333333333333",
        label="AAA-residue",
        codes=[*GOVERNED_CODES, "B1RT_068e737e"],
    )
    assert cc.is_governed_catalogue_version(candidate) is False


def test_a_draft_or_future_version_is_never_the_product_truth() -> None:
    """Scenario E: a future catalogue cannot become the surface by existing."""
    for status in ("DRAFT", "PROPOSED", "SUPERSEDED"):
        future = _candidate(
            version_id="44444444-4444-4444-8444-444444444444",
            label="AAA-future",
            codes=["GP-S4"],
            status=status,
        )
        assert cc.is_governed_catalogue_version(future) is False
        assert (
            cc.select_governed_catalogue_version([future, _governed()])["id"]
            == GOVERNED_VERSION_ID
        )


def test_no_candidate_and_no_governed_candidate_are_both_no_catalogue() -> None:
    """`CS-3`/`IV-4`: no catalogue means no claim, never a guess."""
    assert cc.select_governed_catalogue_version([]) is None
    ungoverned = [
        _candidate(
            version_id="55555555-5555-4555-8555-555555555555",
            label="B1RT-1",
            codes=["B1RT_1"],
        ),
        _candidate(
            version_id="55555555-5555-4555-8555-555555555556",
            label="B3V3-1",
            codes=["B3V3_1", "B3V3_2"],
        ),
    ]
    assert cc.select_governed_catalogue_version(ungoverned) is None
    assert cc.select_governed_catalogue_version([_def1_adversary()]) is None


# ===========================================================================
# 5. Scenario D — a duplicate governed identity fails closed
# ===========================================================================
def _duplicate_of_the_governed_catalogue() -> dict[str, Any]:
    return _governed(
        version_id="66666666-6666-4666-8666-666666666666", label="AAA-duplicate"
    )


def test_a_duplicate_complete_governed_identity_fails_closed() -> None:
    """Two versions claiming the catalogue identity is a governance fault.

    The schema permits it (`UNIQUE (framework_version_id, requirement_code)` is
    per version), so the surface must refuse rather than choose — never silently
    pick one, and never merge the two.
    """
    with pytest.raises(DisclosureViolation) as raised:
        cc.select_governed_catalogue_version(
            [_duplicate_of_the_governed_catalogue(), _governed()]
        )
    message = str(raised.value)
    assert "P17-M2" in message
    assert "ambiguous" in message
    # The refusal names the facts a human needs; it invents no capability value.
    assert GOVERNED_LABEL in message
    for vocabulary in CARBONTALLY_CAPABILITIES:
        assert vocabulary not in message, vocabulary


def test_the_duplicate_refusal_is_order_independent() -> None:
    duplicate = _duplicate_of_the_governed_catalogue()
    for candidates in ([duplicate, _governed()], [_governed(), duplicate]):
        with pytest.raises(DisclosureViolation):
            cc.select_governed_catalogue_version(candidates)


# ===========================================================================
# 6. Selection changes nothing, declares nothing, and cannot upgrade a value
# ===========================================================================
def test_the_selector_returns_the_candidate_unchanged() -> None:
    """No field is added, removed or rewritten — no new vocabulary (`§8`)."""
    governed = _governed()
    before = {key: governed[key] for key in governed}
    selected = cc.select_governed_catalogue_version([governed])
    assert selected is not None
    assert selected == before
    assert selected is not governed  # a copy: the caller cannot mutate the input
    selected["version_label"] = "mutated"
    assert governed["version_label"] == GOVERNED_LABEL


def test_the_identity_helpers_declare_no_new_vocabulary() -> None:
    """`§8`/`AG-6`: no capability, applicability or architecture vocabulary."""
    for function in (
        cc.governed_requirement_identities,
        cc.is_governed_catalogue_version,
        cc.select_governed_catalogue_version,
    ):
        body = inspect.getsource(function)
        for listed in (
            "STRUCTURED_INPUT_REQUIRED",
            "EXTERNAL_INPUT_REQUIRED",
            "NOT_APPLICABLE_TO_PRODUCT",
        ):
            assert listed not in body, (function.__name__, listed)
        # No nested definitions: the helpers add no second rule or vocabulary map.
        assert "\n    def " not in body, function.__name__


def test_the_route_no_longer_implements_the_pre_fix_selection_rule() -> None:
    """Structural guard: the weak rule cannot be reintroduced in the surface.

    `DEF-1` lived in the route; the rule now lives in the governed module only,
    and the route delegates to it instead of inspecting requirement codes.
    """
    from api import v3_disclosure as disclosure_api

    route_source = inspect.getsource(disclosure_api.get_capability_catalogue)
    assert "select_governed_catalogue_version" in route_source
    assert "is_governed_requirement_code" not in route_source
    assert "requirement_codes" not in route_source
    assert "next(" not in route_source


def test_the_def1_adversary_cannot_upgrade_a_governed_value() -> None:
    """The non-upgrading invariant at the selection boundary.

    The governed value for `GP-S3-CAT-01` is `PARTIALLY_SUPPORTED`. The hijack
    candidate records `SUPPORTED` for that same identity; because the candidate is
    never selected, its upgraded row can never enter a claim.
    """
    adversary = _def1_adversary()
    assert adversary["requirement_codes"] == ["GP-S3-CAT-01"]
    assert M1_IMAGE["GP-S3-CAT-01"] == "PARTIALLY_SUPPORTED"
    assert M1_IMAGE["GP-S3-CAT-01"] != "SUPPORTED"
    selected = cc.select_governed_catalogue_version([adversary, _governed()])
    assert selected is not None and selected["id"] != adversary["id"]
    # The complete governed set is selected, so the rollup cannot become 1/0/0/0.
    assert len(selected["requirement_codes"]) == 18
    assert (
        sum(1 for value in M1_IMAGE.values() if value == "SUPPORTED")
        == ROLLUP["SUPPORTED"]
    )
    assert sum(1 for value in M1_IMAGE.values() if value == "PARTIALLY_SUPPORTED") == (
        ROLLUP["PARTIALLY_SUPPORTED"]
    )
