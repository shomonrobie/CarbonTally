"""FIN-06 — Manual Processing governance precedence (pure domain tests).

The PO decision fixes the model: OFF by default, most-specific-wins precedence
``consultant_client > consultant_firm > organization > default(DENY)``, and
absence of an explicit row means DISABLED.
"""
from __future__ import annotations

from domain.manual_processing import (
    DEFAULT_ENABLED,
    SCOPE_CONSULTANT_CLIENT,
    SCOPE_CONSULTANT_FIRM,
    SCOPE_ORGANIZATION,
    SCOPE_PRECEDENCE,
    ManualProcessingGrant,
    OrgContext,
    is_scope_type_valid,
    resolve_effective,
    scope_targets,
)

CLIENT = OrgContext(
    organization_id="org-1", consultant_client_id="cc-1", consultant_firm_id="firm-1"
)
ORG_ONLY = OrgContext(organization_id="org-1")


def _grant(scope_type: str, scope_id: str, enabled: bool) -> ManualProcessingGrant:
    return ManualProcessingGrant(scope_type=scope_type, scope_id=scope_id, enabled=enabled)


class TestScopeVocabulary:
    def test_scope_vocabulary_matches_the_ratified_model(self) -> None:
        assert SCOPE_PRECEDENCE == (
            SCOPE_CONSULTANT_CLIENT,
            SCOPE_CONSULTANT_FIRM,
            SCOPE_ORGANIZATION,
        )
        for scope in SCOPE_PRECEDENCE:
            assert is_scope_type_valid(scope)
        assert not is_scope_type_valid("global")
        assert not is_scope_type_valid("")

    def test_default_is_disabled(self) -> None:
        assert DEFAULT_ENABLED is False

    def test_scope_targets_only_include_known_ids(self) -> None:
        assert scope_targets(ORG_ONLY) == {SCOPE_ORGANIZATION: "org-1"}
        assert scope_targets(CLIENT) == {
            SCOPE_CONSULTANT_CLIENT: "cc-1",
            SCOPE_CONSULTANT_FIRM: "firm-1",
            SCOPE_ORGANIZATION: "org-1",
        }


class TestFailClosedDefault:
    def test_no_rows_means_denied(self) -> None:
        effective = resolve_effective([], ORG_ONLY)
        assert effective.enabled is False
        assert effective.source_level == "default"
        assert effective.source_scope_type is None
        assert effective.default_off is True

    def test_unrelated_rows_do_not_enable(self) -> None:
        effective = resolve_effective([_grant(SCOPE_ORGANIZATION, "org-other", True)], CLIENT)
        assert effective.enabled is False
        assert effective.source_level == "default"


class TestMostSpecificWins:
    def test_organization_grant_enables(self) -> None:
        effective = resolve_effective([_grant(SCOPE_ORGANIZATION, "org-1", True)], ORG_ONLY)
        assert (effective.enabled, effective.source_scope_type) == (True, SCOPE_ORGANIZATION)

    def test_firm_grant_enables_a_client_org(self) -> None:
        effective = resolve_effective(
            [_grant(SCOPE_CONSULTANT_FIRM, "firm-1", True)], CLIENT
        )
        assert (effective.enabled, effective.source_scope_type) == (
            True,
            SCOPE_CONSULTANT_FIRM,
        )

    def test_client_grant_beats_firm_and_organization(self) -> None:
        effective = resolve_effective(
            [
                _grant(SCOPE_ORGANIZATION, "org-1", True),
                _grant(SCOPE_CONSULTANT_FIRM, "firm-1", True),
                _grant(SCOPE_CONSULTANT_CLIENT, "cc-1", True),
            ],
            CLIENT,
        )
        assert effective.source_scope_type == SCOPE_CONSULTANT_CLIENT

    def test_specific_false_overrides_broader_true(self) -> None:
        effective = resolve_effective(
            [
                _grant(SCOPE_ORGANIZATION, "org-1", True),
                _grant(SCOPE_CONSULTANT_FIRM, "firm-1", True),
                _grant(SCOPE_CONSULTANT_CLIENT, "cc-1", False),
            ],
            CLIENT,
        )
        assert effective.enabled is False
        assert effective.source_level == "explicit"
        assert effective.source_scope_type == SCOPE_CONSULTANT_CLIENT

    def test_specific_true_overrides_broader_false(self) -> None:
        effective = resolve_effective(
            [
                _grant(SCOPE_ORGANIZATION, "org-1", False),
                _grant(SCOPE_CONSULTANT_FIRM, "firm-1", True),
            ],
            CLIENT,
        )
        assert effective.enabled is True
        assert effective.source_scope_type == SCOPE_CONSULTANT_FIRM

    def test_firm_scope_does_not_apply_to_a_direct_organization(self) -> None:
        effective = resolve_effective(
            [_grant(SCOPE_CONSULTANT_FIRM, "firm-1", True)], ORG_ONLY
        )
        assert effective.enabled is False
        assert effective.source_level == "default"
