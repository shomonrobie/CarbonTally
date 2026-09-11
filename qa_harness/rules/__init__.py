"""Rule catalogs: business, security, UX, tables, navigation.

Rules are declarative requirements (expected behavior) that the run layer
turns into checks and findings. They are NOT assertions of current state —
historical findings are encoded here as regression targets only.
"""

from qa_harness.rules.business import (
    BusinessRule,
    build_business_rules,
)
from qa_harness.rules.navigation import (
    NavigationRule,
    build_navigation_rules,
)
from qa_harness.rules.security import (
    SecurityRule,
    build_security_rules,
)
from qa_harness.rules.tables import TableRuleEvaluator, build_table_rules
from qa_harness.rules.ux import UxRuleCheck, build_ux_rule_checks

__all__ = [
    "BusinessRule",
    "NavigationRule",
    "SecurityRule",
    "TableRuleEvaluator",
    "UxRuleCheck",
    "build_business_rules",
    "build_navigation_rules",
    "build_security_rules",
    "build_table_rules",
    "build_ux_rule_checks",
]
