"""P12-IMPL-02 — unit tests for organisation-scoped supplier resolution."""
from __future__ import annotations

from engines.supplier_resolution import (
    ACTION_CONFIRM_CREATION,
    ACTION_CONFIRM_MATCH,
    ACTION_MANUAL_REVIEW,
    ACTION_REUSE,
    ACTION_SELECT_CANDIDATE,
    AMBIGUITY_MARGIN,
    VERDICT_AMBIGUOUS,
    VERDICT_EXACT,
    VERDICT_NONE,
    VERDICT_PROBABLE,
    VERDICT_STRONG,
    VERDICT_UNRESOLVED,
    Candidate,
    ResolutionSignals,
    classify,
    name_tokens,
    normalise_identifier,
    normalise_name,
    normalise_postcode,
    score_candidate,
    signals_from_extracted,
)

ORG_A = "org-aaaa"
ORG_B = "org-bbbb"

ROBINSONS = Candidate(
    supplier_id="sup-1",
    organization_id=ORG_A,
    name="Robinsons Recycling Services Ltd",
    postcode="QI14 5ZD",
    vat_number="GB 123 4567 89",
)


def test_normalise_name_strips_legal_forms_and_case():
    assert normalise_name("Robinsons Recycling Services Ltd") == "robinsons recycling services"


def test_normalise_name_treats_ampersand_as_and():
    assert normalise_name("A & B Waste Ltd") == "a and b waste"


def test_normalise_name_handles_none_and_blank():
    assert normalise_name(None) == ""
    assert normalise_name("   ") == ""


def test_name_tokens_returns_comparison_tokens():
    assert name_tokens("Sustainable Direct Group Ltd") == frozenset(
        {"sustainable", "direct", "group"}
    )


def test_normalise_postcode_removes_spacing_and_case():
    assert normalise_postcode("qi14 5zd") == "QI145ZD"


def test_normalise_identifier_strips_separators():
    assert normalise_identifier("GB 123 4567 89") == "GB123456789"


def test_signals_from_extracted_reads_available_keys():
    s = signals_from_extracted({"supplier": "Acme Ltd", "supplier_postcode": "AB1 2CD"})
    assert s.supplier_name == "Acme Ltd"
    assert s.postcode == "AB1 2CD"
    assert s.vat_number == ""


def test_signals_from_extracted_handles_none():
    assert signals_from_extracted(None).usable is False


def test_score_vat_match_is_strongest_signal():
    s = ResolutionSignals(supplier_name="Totally Different Name", vat_number="GB123456789")
    scored = score_candidate(s, ROBINSONS)
    assert scored.score >= 100
    assert "vat_number" in scored.signals


def test_score_requires_both_sides_for_identifier_match():
    s = ResolutionSignals(supplier_name="Robinsons Recycling Services", vat_number="GB999999999")
    scored = score_candidate(s, ROBINSONS)
    assert "vat_number" not in scored.signals


def test_score_exact_name_with_postcode_corroborates():
    s = ResolutionSignals(supplier_name="Robinsons Recycling Services Ltd", postcode="QI145ZD")
    scored = score_candidate(s, ROBINSONS)
    assert "name_exact" in scored.signals
    assert "postcode" in scored.signals
    assert scored.score == 70


def test_score_similar_name_uses_jaccard_threshold():
    s = ResolutionSignals(supplier_name="Robinsons Recycling")
    scored = score_candidate(s, ROBINSONS)
    assert "name_exact" not in scored.signals
    # 2 of 3 tokens shared -> jaccard 0.67 >= 0.5 -> similarity credit, not exact.
    assert scored.score == 20
    assert scored.signals == ["name_similarity:0.67"]


def test_score_no_shared_signals_is_zero():
    s = ResolutionSignals(supplier_name="Unrelated Company")
    assert score_candidate(s, ROBINSONS).score == 0


def test_classify_blank_supplier_requires_manual_review():
    out = classify(ResolutionSignals(supplier_name="   "), [ROBINSONS], ORG_A)
    assert out.verdict == VERDICT_UNRESOLVED
    assert out.action == ACTION_MANUAL_REVIEW
    assert out.auto_persist is False
    assert out.selected is None


def test_classify_no_candidates_requires_confirmed_creation():
    s = ResolutionSignals(supplier_name="Robinsons Recycling Services Ltd")
    out = classify(s, [], ORG_A)
    assert out.verdict == VERDICT_NONE
    assert out.action == ACTION_CONFIRM_CREATION
    assert out.auto_persist is False


def test_classify_cross_tenant_candidate_is_rejected_and_not_selected():
    """Org A must never resolve to Org B's supplier (tenant isolation)."""
    s = ResolutionSignals(
        supplier_name="Robinsons Recycling Services Ltd",
        postcode="QI145ZD",
        vat_number="GB123456789",
    )
    foreign = Candidate(
        supplier_id="sup-other",
        organization_id=ORG_B,
        name="Robinsons Recycling Services Ltd",
        postcode="QI14 5ZD",
        vat_number="GB123456789",
    )
    out = classify(s, [foreign], ORG_A)
    assert out.verdict == VERDICT_NONE
    assert out.selected is None
    assert out.rejected == [
        {"supplier_id": "sup-other", "reason": "cross_tenant_candidate"}
    ]


def test_classify_exact_name_plus_postcode_auto_reuses():
    s = ResolutionSignals(
        supplier_name="Robinsons Recycling Services Ltd", postcode="QI14 5ZD"
    )
    out = classify(s, [ROBINSONS], ORG_A)
    assert out.verdict == VERDICT_EXACT
    assert out.action == ACTION_REUSE
    assert out.auto_persist is True
    assert out.selected is ROBINSONS


def test_classify_vat_match_is_exact_and_reusable():
    s = ResolutionSignals(supplier_name="Robinsons", vat_number="GB123456789")
    out = classify(s, [ROBINSONS], ORG_A)
    assert out.verdict == VERDICT_EXACT
    assert out.action == ACTION_REUSE
    assert out.auto_persist is True


def test_classify_exact_name_without_corroboration_requires_confirmation():
    s = ResolutionSignals(supplier_name="Robinsons Recycling Services Ltd")
    out = classify(s, [ROBINSONS], ORG_A)
    assert out.verdict == VERDICT_STRONG
    assert out.action == ACTION_CONFIRM_MATCH
    assert out.auto_persist is False
    assert out.selected is ROBINSONS


def test_classify_ambiguous_candidates_require_selection():
    """Two plausible suppliers within the margin must never be auto-chosen."""
    twin = Candidate(
        supplier_id="sup-2",
        organization_id=ORG_A,
        name="Robinsons Recycling Services Ltd",
        postcode="QI14 5ZE",
    )
    s = ResolutionSignals(supplier_name="Robinsons Recycling Services Ltd")
    out = classify(s, [ROBINSONS, twin], ORG_A)
    assert out.verdict == VERDICT_AMBIGUOUS
    assert out.action == ACTION_SELECT_CANDIDATE
    assert out.auto_persist is False
    assert out.selected is None
    assert f"< {AMBIGUITY_MARGIN}" in out.reason


def test_classify_clear_winner_is_not_ambiguous():
    weak = Candidate(
        supplier_id="sup-3", organization_id=ORG_A, name="Robinsons Recycling Services"
    )
    s = ResolutionSignals(
        supplier_name="Robinsons Recycling Services Ltd", postcode="QI14 5ZD"
    )
    out = classify(s, [ROBINSONS, weak], ORG_A)
    assert out.verdict == VERDICT_EXACT
    assert out.selected is ROBINSONS


def test_classify_similar_only_match_is_probable_and_never_auto_persists():
    similar = Candidate(
        supplier_id="sup-4",
        organization_id=ORG_A,
        name="Robinsons Recycling Services Group Ltd",
    )
    s = ResolutionSignals(supplier_name="Robinsons Recycling Services Ltd")
    out = classify(s, [similar], ORG_A)
    assert out.verdict == VERDICT_PROBABLE
    assert out.action == ACTION_CONFIRM_MATCH
    assert out.auto_persist is False


def test_classify_never_auto_persists_for_non_exact_verdicts():
    cases = [
        (ResolutionSignals(supplier_name=""), [ROBINSONS]),
        (ResolutionSignals(supplier_name="Robinsons Recycling Services Ltd"), []),
        (
            ResolutionSignals(supplier_name="Robinsons Recycling Services Ltd"),
            [ROBINSONS],
        ),
        (ResolutionSignals(supplier_name="Unrelated"), [ROBINSONS]),
    ]
    for signals, candidates in cases:
        out = classify(signals, candidates, ORG_A)
        assert out.verdict != VERDICT_EXACT
        assert out.auto_persist is False


def test_outcome_as_dict_is_auditable():
    s = ResolutionSignals(
        supplier_name="Robinsons Recycling Services Ltd", postcode="QI14 5ZD"
    )
    payload = classify(s, [ROBINSONS], ORG_A).as_dict()
    assert payload["verdict"] == VERDICT_EXACT
    assert payload["selected_supplier_id"] == "sup-1"
    assert payload["signals"]["supplier_name"] == "Robinsons Recycling Services Ltd"
    assert payload["candidates"][0]["score"] == 70


def test_classify_equal_scores_are_ambiguous_not_order_dependent():
    """Equal-score candidates must never be silently chosen by list order."""
    a = Candidate(supplier_id="sup-a", organization_id=ORG_A, name="Acme Waste Ltd")
    b = Candidate(supplier_id="sup-b", organization_id=ORG_A, name="Acme Waste Ltd")
    s = ResolutionSignals(supplier_name="Acme Waste Ltd", postcode="AB1 2CD")
    assert classify(s, [b, a], ORG_A).verdict == VERDICT_AMBIGUOUS
    assert classify(s, [a, b], ORG_A).verdict == VERDICT_AMBIGUOUS


def test_multi_year_reuse_resolves_to_single_supplier_id():
    """FY2025 and FY2026 documents for one supplier reuse a single supplier id."""
    fy25 = ResolutionSignals(
        supplier_name="Robinsons Recycling Services Ltd", postcode="QI14 5ZD"
    )
    fy26 = ResolutionSignals(
        supplier_name="ROBINSONS RECYCLING SERVICES LIMITED", postcode="QI145ZD"
    )
    first = classify(fy25, [ROBINSONS], ORG_A)
    second = classify(fy26, [ROBINSONS], ORG_A)
    assert first.selected.supplier_id == second.selected.supplier_id == "sup-1"
    assert first.action == second.action == ACTION_REUSE
    assert first.verdict == second.verdict == VERDICT_EXACT


def test_company_number_match_is_exact_across_naming_variants():
    s = ResolutionSignals(supplier_name="Robinsons", company_number="01234567")
    cand = Candidate(
        supplier_id="sup-co",
        organization_id=ORG_A,
        name="Robinsons Recycling Services Ltd",
        company_number="01234567",
    )
    out = classify(s, [cand], ORG_A)
    assert out.verdict == VERDICT_EXACT
    assert out.selected.supplier_id == "sup-co"


def test_cross_tenant_candidate_never_outranks_own_org_candidate():
    foreign = Candidate(
        supplier_id="sup-foreign",
        organization_id=ORG_B,
        name="Robinsons Recycling Services Ltd",
        postcode="QI14 5ZD",
        vat_number="GB123456789",
    )
    s = ResolutionSignals(
        supplier_name="Robinsons Recycling Services Ltd", postcode="QI14 5ZD"
    )
    out = classify(s, [foreign, ROBINSONS], ORG_A)
    assert out.selected.supplier_id == "sup-1"
    assert out.rejected == [
        {"supplier_id": "sup-foreign", "reason": "cross_tenant_candidate"}
    ]
