"""Demo identity population model.

Encodes the deterministic identity scheme from
``tools/seed_investor_demo/DEMO_IDENTITIES.md`` so the harness can reason
about the COMPLETE population (1185 demo identities), not just 13
representative personas. Passwords are never stored or logged — the single
shared password is resolved at run time by
:mod:`qa_harness.core.credentials` (environment override, then the
gitignored ``.local-demo-credentials.md`` file).
"""

from qa_harness.identities.loader import (
    DEMO_DOMAIN,
    Identity,
    IdentityLoader,
    load_identity_population,
)
from qa_harness.identities.resolver import IdentityResolver, ResolveError
from qa_harness.identities.selectors import (
    RepresentativeSelector,
    cross_boundary_pairs,
    select_by_role,
)

__all__ = [
    "DEMO_DOMAIN",
    "Identity",
    "IdentityLoader",
    "IdentityResolver",
    "RepresentativeSelector",
    "ResolveError",
    "cross_boundary_pairs",
    "load_identity_population",
    "select_by_role",
]
