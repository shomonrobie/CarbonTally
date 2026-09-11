# REPOSITORY STRATEGY
### Layout, package names, versioning, CI/CD, contribution and licensing for the open-source release

**Status:** PROPOSAL — for Product Owner review. No code changed.

---

## 1. The three candidate layouts (Part 18)

### Option A — two independent repositories

```
github.com/<org>/saas-qa-harness
github.com/<org>/saas-audit-swarm
(+ github.com/<org>/saas-assurance-contracts — required because both tools
   must agree on EvidencePacket/Finding/ApplicationProfile)
```

| criterion | verdict |
|---|---|
| maintainability | two release trains, two issue trackers, contract repo must version-lock (drift risk) |
| user experience | two installs, two docs; clear tool identity |
| installation complexity | higher (3 packages, pinned versions) |
| security | independent; but shared-contract trust boundary is remote |
| dependency isolation | strongest (no cross-tool imports possible) |
| AI optionality | independent |
| release/versioning | fully independent — good for community, bad for atomic changes |
| community contribution | two focused communities; contracts repo often neglected |
| CI/CD | three pipelines to keep aligned |
| future extensibility | new tools (e.g. a runtime-monitor) must join the contract scheme manually |

### Option B — one monorepo with two packages (+ contracts)

```
github.com/<org>/saas-assurance
├── packages/contracts      # saas-assurance-contracts
├── packages/qa-harness     # saas-qa-harness
├── packages/audit-swarm    # saas-audit-swarm
└── profiles/               # carbontally (reference), acme-notes (example)
```

| criterion | verdict |
|---|---|
| maintainability | one issue tracker, one PR surface, atomic cross-package changes |
| user experience | one repo/install story; two independent CLIs |
| installation complexity | low — install only the package(s) you need |
| security | single release surface to scan; shared CI secret scan |
| dependency isolation | per-package `pyproject.toml`; contracts has zero runtime deps |
| AI optionality | qa-harness has no AI dependency at all |
| release/versioning | per-package versions; a `saas-assurance` metapackage optional |
| community contribution | contributors land one PR touching both sides cleanly |
| CI/CD | one pipeline, per-package jobs; shared self-test + secret scan |
| future extensibility | add `packages/regression-monitor` etc. under the same contracts |

### Option C — one core framework with qa/audit modules

```
github.com/<org>/saas-qa-framework
├── core/   (engine shared by both)
├── qa/     (harness module)
└── audit/  (swarm module)
```

| criterion | verdict |
|---|---|
| maintainability | strongest code reuse, but forces one install surface for both tools |
| user experience | one tool with two modes — conflicts with "independently usable" |
| installation complexity | lowest (one package) |
| security | single trust domain; larger blast radius per release |
| dependency isolation | weak — audit's AI deps leak into the harness install unless extras are perfect |
| AI optionality | compromised — AI must be an optional extra of a shared engine |
| release/versioning | single version; harness and swarm can't move independently |
| community contribution | blurry boundary — hard to say "this PR is for the QA tool" |
| CI/CD | simplest |
| future extensibility | easiest to add modules, hardest to keep them independent |

## Recommendation: **Option B — monorepo `saas-assurance` with three
packages** (`contracts`, `qa-harness`, `audit-swarm`)

Rationale:
- It keeps the two tools **independently usable** (the PO's hard
  requirement) while giving one place for shared contracts and atomic
  cross-tool changes.
- It is a strict superset of Option A: after the contracts stabilize, each
  package can be split into its own repository with near-zero migration
  (the contracts package is already a publishable unit).
- It avoids Option C's coupling trap: the QA Harness stays **zero-AI**, the
  Audit Swarm stays **AI-optional**, and dependency isolation is enforced by
  per-package `pyproject.toml` (tested in CI by importing each package in a
  clean venv).

## Package names (Python + CLI)

| package (PyPI) | import root | CLI entry points |
|---|---|---|
| `saas-assurance-contracts` | `saas_assurance_contracts` | — |
| `saas-qa-harness` | `saas_qa_harness` | `qa-harness`, `saas-assurance run-qa` |
| `saas-audit-swarm` | `saas_audit_swarm` | `audit-swarm`, `saas-assurance analyze` |

(Optional `saas-assurance` metapackage installs all three and provides the
unified CLI.)

---

## 2. Versioning

- **SemVer 2.0** per package; a shared `contracts` version is bumped only
  when the schema changes.
- Schema changes: additive fields → minor; breaking renames → major with a
  deprecation window of two minor versions.
- A `contracts/CHANGELOG.md` entry is mandatory for every schema change;
  the compatibility mapping table (see
  `SHARED_EVIDENCE_FINDING_CONTRACT.md` §5) is kept in sync.

---

## 3. CI/CD (one pipeline, per-package jobs)

1. **self-tests** — `pytest` per package (deterministic, no app contact;
   qa-harness has ~33 test files, audit-swarm has 146 tests).
2. **isolation test** — install each package in a clean venv; assert the
   harness imports without audit-swarm deps (and vice versa).
3. **secret scan** — `gitleaks`/`trufflehog` on every PR (see
   `OPEN_SOURCE_SECURITY_CHECKLIST.md` §5).
4. **redaction smoke** — run a tiny fake-profile run; assert no secret
   strings in stdout/stderr/report files.
5. **profile parity** — for the reference profile: run the CarbonTally
   profile; diff findings/evidence hashes against the frozen baseline
   (the MIGRATION_PLAN compatibility gate).
6. **dependency audit** — `pip-audit` / `osv-scanner`.
7. **docs build** — validate all examples in TUTORIAL.md.

---

## 4. Community contribution

- `CONTRIBUTING.md` with the "generic engine vs profile data" rule: new
  product knowledge must land in `profiles/`, never in `packages/*`.
- Issue labels: `engine`, `profile:carbontally`, `contracts`, `docs`.
- PR template requires: classification (engine/profile/docs), tests, and a
  statement that no secret was introduced.
- CarbonTally profile changes are reviewed by the CarbonTally PO; engine
  changes are reviewed by maintainers.

---

## 5. Licensing (Part 19)

| license | fit for "free, open-source, reusable SaaS QA/assurance tooling" |
|---|---|
| MIT | permissive, simplest, no patent grant; fine but weaker for contributors |
| **Apache-2.0 (recommended)** | permissive, explicit **patent grant**, explicit trademark notice rules, safe for commercial consumers and enterprises; the community default for infra/dev tooling |
| GPL-3.0 / LGPL / AGPL | copyleft — deters embedded/private use, incompatible with many SaaS vendors' legal policies; AGPL especially hostile to "run against my SaaS" tooling |

**Recommendation: Apache-2.0.**
- Consumers (incl. CarbonTally itself) can embed/redistribute with
  attribution and no copyleft obligations.
- Contributors get patent protection.
- It matches how comparable tools (pytest ecosystem, Playwright deps,
  OpenRouter SDK) are licensed.
- MIT is an acceptable fallback if the PO prefers maximum simplicity; the
  GPL family is not recommended for this audience.

The license file is **not added** by this audit — the PO decides.

---

## 6. Decision summary

1. Layout: **Option B monorepo** (`saas-assurance`), three packages.
2. CarbonTally becomes `profiles/carbontally/` inside the monorepo (or a
   separate private package if the PO prefers — see MIGRATION_PLAN PHASE 11).
3. License: **Apache-2.0** (PO decision required).
4. Both tools remain **independently installable and independently usable**;
   they interoperate through `saas-assurance-contracts`.
5. The fictional reference profile (`profiles/acme-notes/`) proves the tools
   work without CarbonTally.

*End of REPOSITORY_STRATEGY.md.*
