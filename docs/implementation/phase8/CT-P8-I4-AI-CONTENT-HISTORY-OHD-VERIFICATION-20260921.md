# CT-P8-I4-AI-CONTENT-HISTORY-OHD-VERIFICATION-20260921

**Task:** independent verification of the factual and architectural findings in the two Cline analyses of `public.ai_content_history`:
1. `CT-P8-I4-AI-CONTENT-HISTORY-ORIGIN-FORENSIC-20260921.md`
2. `CT-P8-I4-AI-CONTENT-HISTORY-INSIGHT-SCHEMA-FIT-20260921.md`

**Authority:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Starting HEAD:** `123cc3a6bbaece5ed9793d97eab499cfcb6fcdae` · **Remote:** `github/p8-release-reconciled` (aligned `0 0`) · **Working tree at start:** clean, no stash.

**Scope discipline:** no application code, migration, schema, test, configuration, Master Specification or other document was modified; no table was renamed, dropped or created; no data was migrated or deleted; no RLS policy or permission was changed; **no production database was queried**. One read-only inspection of the **local Demo Lab** database (`carbontally_demo_local`) was performed to test two claims against a live environment; it changed nothing. The only repository change is this report.

**Verification labels used below:**
`Cline finding` = what the analysed report asserts · `OHD verified` = reproduced independently by this task · `OHD cannot establish` = not decidable from repository evidence.

---

## 1. Verification scope

The question under test is **not** "should CarbonTally reuse or delete `ai_content_history`". It is:

> Are Cline's historical and schema-fit findings independently supported by the repository, and is the conclusion that direct reuse of the existing table is inappropriate adequately supported?

This report therefore (a) reproduces the factual claims, (b) classifies each as `VERIFIED` / `PARTIALLY VERIFIED` / `NOT VERIFIED` / `CONTRADICTED` / `UNKNOWN / NOT REPOSITORY-VERIFIABLE`, and (c) reports discrepancies. It decides nothing. It does **not** "CLOSE" or "APPROVE" Q1, does **not** approve reuse, deletion or migration, and does **not** authorize I4.

## 2. Starting repository state

| Item | Value | Result |
|---|---|---|
| Checkout | `/home/shomonrobie/ct_93d5cdd` | ✅ authoritative Phase 8 checkout |
| Branch | `p8-release-reconciled` (not switched during this task) | ✅ |
| Starting HEAD | `123cc3a6bbaece5ed9793d97eab499cfcb6fcdae` | ✅ exact |
| Remote alignment | `github/p8-release-reconciled` = same SHA; `0 0` | ✅ |
| Working tree | `git status --porcelain --untracked-files=all` → empty | ✅ clean |
| Stash | none | ✅ |
| `origin` remote | stale local path `/tmp/ct_step2` — not used as evidence | ✅ |
| Recent history | `123cc3a` schema-fit analysis · `2c67a31` origin forensic · `fca5469` I4 pre-authorization audit · `875e04e` Insight v1.1 + I3 closure · `7faaa57` OHD I3 re-verification | ✅ |

**Analysis-only confirmation:** `git diff --name-only 2c67a31^ 123cc3a -- . ':!docs/**'` → empty, and each commit changes exactly one markdown file (367 / 409 insertions). The I4 audit commit `fca5469` is likewise documentation-only. **Scope discipline of the analysed work is `VERIFIED`.**

## 3. Documents reviewed

Cline reports (both read in full): the origin forensic (367 lines) and the schema-fit analysis (409 lines).

Independently inspected evidence: `supabase/migrations/00000000000000_init_schema.sql`; `supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql`; `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql`; `20261001000000_p8_i1_insight_persistence.sql`; `20261002000000_p8_i2_insight_authorization.sql`; `supabase/seed.sql`; `CarbonTally_DB_Schema_V3M2.sql` (root dump); `prisma/schema.prisma`; `e2e/environment/supabase/migrations/**`; `database/rc1/004_rc1_rls.sql`; `tools/carbon_data_factory/schema.txt`; `docs/Final/UI_UX-Final_Guideline.md`; `docs/Final_Kimi/**`; `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md`; `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md`; `docs/verification/QA-AI-001-*.md`; `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`; `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md`; `docs/implementation/phase8/CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921.md`; `backend/domain/audit.py`, `backend/api/insight_authz.py`, `backend/services/insight_tools.py`, `backend/domain/insight_tool.py`; Insight I1–I3 tests; Git history across all refs. Plus a read-only inspection of the local Demo Lab database.

## 4. Historical origin verification

**Cline finding** — the table is a legacy pre-Phase-8 AI-content journal carried into the V3 baseline from the RC1/RC2 (V1/V2-era) design; it enters this repository inside the monolithic V3 initial schema.

**OHD verified** — **`VERIFIED`.** The only `CREATE TABLE` for the table in the migration tree is `supabase/migrations/00000000000000_init_schema.sql:1041` (a second copy exists at `e2e/environment/supabase/migrations/00000000000000_init_schema.sql:1041`). The introducing commit is a baseline commit, not a phase migration. The RC1 bundle `database/rc1/004_rc1_rls.sql:137` enumerates the table in its RLS table array, committed `de94363` / `9f87229` on **2026-08-04** — **two days before** the baseline commit that creates it — so the table demonstrably pre-dates this repository's baseline, as Cline infers.

**OHD cannot establish** — the original V1/V2 authoring task or phase: the pre-baseline database history is not in this repository. Cline states this limitation correctly.

## 5. Creation migration verification

| Item | Cline finding | OHD verified |
|---|---|---|
| Migration file | `supabase/migrations/00000000000000_init_schema.sql` | `VERIFIED` |
| Creation lines | 1041–1060 | `VERIFIED` (`CREATE TABLE` at :1041, `COMMENT ON TABLE` at :1060) |
| Section banner | `-- PHASE D3 CONTINUED: AI CONTENT` at :1038 | `VERIFIED` (line 1038) |
| Original schema | 16 columns, quoted verbatim | `VERIFIED` — DDL matches the quote exactly, including every `CHECK` |
| Original comment | `'AI generation history'` | `VERIFIED` |
| Altered since? | No | `VERIFIED` by direct inspection (see §9) |

The shipped DDL (unchanged to HEAD) is 16 columns: `id`, `organization_id` (NOT NULL, FK→`organizations` ON DELETE CASCADE), `report_id` (nullable uuid), `prompt_type` (varchar NOT NULL), `prompt_text`, `model_used`, `generated_content`, `content_format`, `tokens_used`, `processing_time_ms`, `cost`, `user_rating`, `user_feedback`, `was_accepted`, `created_at`, `created_by`.

**OHD addition (`Cline finding` incomplete):** the table has **three divergent in-repository declarations** — the SQL baseline (above), a root-level pg-style dump `CarbonTally_DB_Schema_V3M2.sql` (`:313` `CREATE TABLE IF NOT EXISTS`, `:340` comment), and a **Prisma model** `prisma/schema.prisma:599`. Neither the dump nor the Prisma model appears in the reports' reference inventories (see §21).

## 6. Introducing commit verification

**Cline finding** — `2d23fb892921cbc41d6c0c20b7660e86fc968178`, "CarbonTally RC2 Final database baseline".

**OHD verified** — **`VERIFIED` exactly.** `git log --diff-filter=A` on that file returns only `2d23fb892921cbc41d6c0c20b7660e86fc968178`, author `shomonrobie <38324907+shomonrobie@users.noreply.github.com>`, date `2026-08-06 06:42:42 -0700`, subject `CarbonTally RC2 Final database baseline`. `git blame -L 1041,1060` attributes **all 20 creation lines** to `2d23fb89`. The banner line 1038 is blamed to `dbe72aa6` (2026-08-14) — i.e. added **eight days after** creation, as Cline states. `git log --follow` on the file returns exactly the 4 commits Cline lists (`eed55d6`, `2d23fb8`, `d3af816`, `dbe72aa`).

## 7. Original purpose verification

**Cline finding** — the documented purpose is "Track AI-generated content with feedback", associated with report generation.

**OHD verified** — **`VERIFIED`**, every quoted artefact reproduced with matching line numbers:

* `docs/Final/UI_UX-Final_Guideline.md:495–531` — `-- TABLE: ai_content_history` / `-- Purpose: Track AI-generated content with feedback`; the block declares `report_id UUID REFERENCES report_generation_queue(id)`, `prompt_type VARCHAR(50) NOT NULL, -- 'executive_summary', 'analysis', 'methodology'`, `was_accepted BOOLEAN DEFAULT TRUE`, `created_by UUID REFERENCES organization_members(id)` and two indexes `idx_ai_history_org` / `idx_ai_history_report`. Index entry `:958` reads `ai_content_history → Track AI-generated content`. That document was added in the **same** baseline commit `2d23fb8`.
* `docs/Final_Kimi/…/01_application_architecture.md:133`, `03_module_breakdown.md:277` ("Prompt/response audit"), `04_api_design.md:247` (per-report provenance "model, tokens, cost").
* `CarbonTally_RC2_Architecture_Freeze.md:284` → `| ai_content_history | — all columns | KEEP | |`.
* `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md:106` → "AI usage + cost already captured — `ai_content_history` (tokens, cost, …)".

**Per-field verification:** `report_id` ✓ shipped (nullable, no FK); `prompt_type` ✓ shipped NOT NULL; `generated_content`, `model_used`, `tokens_used`, `processing_time_ms`, `cost`, `user_rating`, `user_feedback`, `was_accepted` ✓ all shipped. The design's inline FKs (`report_id`, `created_by`) and its two indexes were **not shipped in the SQL baseline** ✓ (independently confirmed in §9/§14).

**OHD correction (minor):** Cline attributes the "16-column" characterisation to `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md:47`; line 47 is a table header, and the actual `ai_content_history (16)` count is at **:76**. The substantive claim (16 = column count, not rows) is `VERIFIED`.

**OHD note:** the purpose claim is supported for the **design** and for legacy documentation. The reports correctly stop short of claiming that this purpose was ever exercised by code in this repository (§8).

## 8. Historical usage verification

**Cline finding** — no application code ever read or written the table; no ORM/class ever existed.

**OHD verified — writer/reader claim: `VERIFIED`. ORM claim: `CONTRADICTED`.**

Reproduced over **all refs**, then re-run excluding the two Cline report commits (whose text contains the search strings and therefore pollutes `-S` — see §21):

| Pattern | All refs | Excluding the two reports | Finding |
|---|---|---|---|
| `AIContentHistory` | 1 | **0** | no such class ✓ |
| `aiContentHistory` | 1 | **0** | no such identifier ✓ |
| `INSERT INTO ai_content_history` | 1 | **0** | no writer ✓ |
| `INSERT INTO public.ai_content_history` | 1 | **0** | no writer ✓ |
| `UPDATE public.ai_content_history` | 1 | **0** | no updater ✓ |
| `delete from ai_content_history` | 1 | **0** | no deleter ✓ |
| `FROM public.ai_content_history` | 1 | **0** | no qualified reader ✓ |
| `FROM ai_content_history` | 2 | **1** | the single hit is the Phase 8 QA command `SELECT count(*) FROM ai_content_history` in QA-AI-001 ✓ |
| `ai_content_history` (any) | 26 | 24 | Cline reported 24 ✓ |
| files ever named `*ai_content*` | — | **0** | ✓ |
| Supabase-client forms `.from('ai_content_history')` / `.table('ai_content_history')` | — | **0** | no client-side consumer ✓ |

**`CONTRADICTED` — the ORM/model claim.** `prisma/schema.prisma:599` declares `model ai_content_history { … }` with all 16 fields, three relations (`organizations` via `organization_id`, `organization_members` via `created_by`, `report_generation_queue` via `report_id`) and **two `@@index` declarations** mapping to the design's `idx_ai_history_org` and `idx_ai_history_report` (lines 620–621); four further models carry `ai_content_history[]` back-relations (`:2083`, `:2236`, `:2667`, and the model's own relations). Prisma is a declared dependency of this repository (root `package.json`: `"prisma": "^6.12.0"`, `"@prisma/client": "^7.9.1"`) and `seed.config.ts:13` instantiates `PrismaClient`. The forensic report's claim "no ORM/model class ever existed" (and evidence row 22) is therefore **not supported**: a tracked ORM schema declares the model. The **substantive** claim survives in weaker form — **no Prisma client code and no Python application code touches this model or table**, so "no application writer or reader in this repository" remains `VERIFIED`.

**OHD cannot establish** — whether any external or legacy writer still targets the table. Cline flags this correctly.

## 9. Historical alteration verification

**Cline finding** — never altered; no `ALTER TABLE`, no `ADD COLUMN`; no trigger; no index.

**OHD verified** — **`VERIFIED` on substance, with a methodological correction (`PARTIALLY VERIFIED` as stated).**

Direct inspection of the whole repository: **0** `ALTER TABLE public.ai_content_history` statements, **0** `ADD COLUMN` statements, **0** `CREATE INDEX … ai_content_history`, **0** occurrences of `idx_ai_history` in any `.sql`, **0** non-internal triggers on the table in the live local database. No drop, no recreation, no rename, no superseding migration.

**Correction 1 (self-polluting method).** The cited command `git log --all -S'ALTER TABLE public.ai_content_history'` returns **1**, not 0: the single match is commit `2c67a31` — **the forensic report itself**, which contains that literal string. The same applies to `-S'ai_content_history ADD COLUMN'` (1 = the report) and to every `AIContentHistory`/`INSERT`/`UPDATE`/`delete` count in §7–§8 of the forensic report. The reported finds were true when written, but the method is not reproducible now because the report pollutes its own search. Excluding the report commits, all counts return to 0 (`VERIFIED` substance).

**Correction 2 (quoted/line-wrapped forms are invisible to the cited pattern).** The root dump contains `ALTER TABLE ONLY "public"."ai_content_history" ADD CONSTRAINT …` at `:3243-3244` and `:4285-4286`, which the unquoted single-line pattern cannot match. These are constraint declarations in a reconstruction dump, not column alterations, so the substance ("the table's definition was never altered") stands.

## 10. Phase association verification

**Cline finding** — not a Phase 1–7 creation, not a Phase 8 creation, originated in the RC2 baseline; `PHASE D3 (AI CONTENT)` is a schema-build section, not a product phase.

**OHD verified** — **`VERIFIED`.** All nine banners exist at exactly the cited lines (`:9 PHASE D1`, `:182 D2`, `:614 D3`, `:777 D3 CONTINUED: PROCESSING & QUEUE`, `:944 D3 CONTINUED: REPORTS`, `:1038 D3 CONTINUED: AI CONTENT`, `:1063 D4`, `:1644 D4 CONTINUED: LOGS & AUDIT`, `:2133 D5 CONSTRAINTS & INDEXES`), and they are construction sections of the V3 database baseline (D1→D5), not product phases. The banner was added 2026-08-14 by `dbe72aa6`, eight days after the table itself. The timeline Cline gives (2026-08-04 RC1 bundle → 2026-08-06 creation → 2026-08-14 banner → 2026-09-15 RLS enablement → 2026-09-21 I1/I2 disclaimers) is reproduced. No artefact associates the table with product Phases 1–7, and it predates Phase 8 by roughly five weeks.

**OHD cannot establish** — whether authorship belonged to a V1 or V2 development phase. Cline preserves this uncertainty correctly.

## 11. Current usage verification

**Cline finding** — no runtime application path references it; current-tree references are DDL, the RLS array, I1/I2 comments and tests, seed header, data-factory schema text and documentation.

**OHD verified** — **`VERIFIED` for the runtime-usage conclusion; `PARTIALLY VERIFIED` for the reference inventory (three omissions).**

Reproduced by grep over the current tree: the only non-documentation references are
`supabase/migrations/00000000000000_init_schema.sql:1041,1060` (DDL); `20260925000000_p8_rls_4b_group1_enablement.sql:80` (RLS array); `20261001000000_…:24` and `20261002000000_…:28` (I1/I2 "does not touch" comments); `backend/tests/unit/data/test_i1_insight_migration.py:17,134` and `test_i2_insight_authorization_contracts.py:111` (**negative** assertions); `supabase/seed.sql:181`; `tools/carbon_data_factory/schema.txt:1041,1060`; `database/rc1/004_rc1_rls.sql:137`. **No** `backend/data/**` repository, `backend/services/**` service, `backend/api/**` route, worker, job, frontend module or fixture exists. The only current readers/writers of the name are tests asserting the table is *not* used.

**Omisions found in the reports' inventories (`PARTIALLY VERIFIED`):**
1. `prisma/schema.prisma` (ORM model + relations + indexes) — see §8.
2. `CarbonTally_DB_Schema_V3M2.sql` — the root dump that carries the **RLS policies** (§15) and constraint statements.
3. `e2e/environment/supabase/migrations/00000000000000_init_schema.sql:1041` — a second copy of the DDL (the e2e tree's 68 `CREATE POLICY` statements include none for this table).

The seed claim is `VERIFIED` independently: `supabase/seed.sql` contains **134** `Data for Name:` headers and **0** `COPY` data blocks — it is header-only and data-stripped, so it neither seeds nor populates the table.

## 12. Production-data limitation

**Cline finding** — `PRODUCTION ROW PRESENCE NOT VERIFIED`; the only observation is 0 rows in the local demo database (`[OBS]`, QA-AI-001).

**OHD verified** — **`VERIFIED`, and the report's restraint is correct.** The cited QA artefacts exist as quoted (`QA-AI-001:101, :202, :370, :392, :515, :560`), the measurement was a read-only `SELECT count(*) FROM ai_content_history` against `carbontally_demo_local` (Demo Lab, 136 tables), and the feature audit repeats "dormant (0 rows, no application reference)" at `:200`.

**OHD independent corroboration (local, not production):** a read-only query of `carbontally_demo_local` returned **0 rows** — consistent with the cited observation.

**Distinctions preserved, as required:**

| Dimension | State |
|---|---|
| Repository consumers | **verified** (none) |
| Repository schema declarations | **verified** (three, divergent — §5/§21) |
| Local demo rows | **verified** (0) |
| Production rows | **unknown** — not measured, and this task did not query production |
| External/legacy writers | **unknown** |
| Live RLS policy state outside the local demo DB | **unknown** for other environments (verified only for the local Demo Lab) |

## 13. Full schema-fit verification

Column-by-column result for the schema-fit matrix (`Cline finding` → `OHD verified`):

| # | Column | Cline classification | OHD assessment |
|---|---|---|---|
| 1 | `id` | reusable (generation identity) | `VERIFIED` — generic PK |
| 2 | `organization_id` | reusable, matches I1 tenant key | `VERIFIED` — NOT NULL + cascade FK, same pattern as I1 |
| 3 | `report_id` | report-specific | `VERIFIED` (see §14) |
| 4 | `prompt_type` | report-specific (NOT NULL, report-section vocabulary) | `VERIFIED` — NOT NULL with `'executive_summary'/'analysis'/'methodology'` semantics and no CHECK |
| 5 | `prompt_text` | partly | `VERIFIED` — generic storage, but privacy posture open (Master Spec §41) |
| 6 | `model_used` | reusable but insufficient (no provider, no version) | `VERIFIED` — the DDL has no provider and no version column |
| 7 | `generated_content` | reusable for generation evaluation | `VERIFIED` |
| 8 | `content_format` | partly | `VERIFIED` — generic format metadata |
| 9 | `tokens_used` | reusable nullable telemetry | `VERIFIED` (CHECK ≥ 0) |
| 10 | `processing_time_ms` | reusable | `VERIFIED` |
| 11 | `cost` | reusable but duplicates other homes | `VERIFIED` (see §17) |
| 12 | `user_rating` | reusable, uniquely | `VERIFIED` (CHECK 1–5) |
| 13 | `user_feedback` | reusable, uniquely | `VERIFIED` |
| 14 | `was_accepted` | reusable, uniquely | `VERIFIED` |
| 15 | `created_at` | reusable but weaker than I1 | `VERIFIED` — nullable, default `NOW()` (I1 uses NOT NULL) |
| 16 | `created_by` | partly — nullable, no FK, no predicate | `VERIFIED` in SQL; **see §14/§21** — the Prisma declaration does assert a `created_by` relation and a default for `was_accepted` |

Missing discriminators claimed by Cline — conversation/message link, interaction identity, intent, tool-call/reference fields, answer status, provider, model version, finish reason, correlation identifier: **`VERIFIED`** — none is present in the shipped DDL.

**The aggregate claim "13 of 16 columns are non-report-specific" — `PARTIALLY VERIFIED` (interpretation-dependent).**
The arithmetic is consistent with Cline's own matrix: 16 columns minus 2 fully report-specific (`report_id`, `prompt_type`) minus 1 partly report-flavoured (`content_format`) = 13. But the boundary is judgemental: treating `prompt_type` as report-specific *and* `content_format`/`prompt_text` as report-flavoured yields **12**; treating only `report_id`/`prompt_type` as report-specific yields **14**. The defensible range is therefore **12–14**, and Cline's 13 is a reasonable but interpretive point estimate rather than a fact. Its own definition ("semantically usable … not 'usable without schema work'") is stated honestly. OHD records the range rather than forcing agreement.

## 14. `report_id` verification

**Cline finding** — no shipped FK, no index, nullable, semantic-only linkage, report-centric intent.

**OHD verified** — **`VERIFIED` for the SQL baseline, the root dump and the live local database; `PARTIALLY VERIFIED` for the repository as a whole.**

| Check | Result |
|---|---|
| Shipped FK in migrations | **none** (`report_id UUID`, bare) ✓ |
| FK in the root dump | **none** (only `ai_content_history_organization_id_fkey`) ✓ |
| FK in the live local Demo Lab DB | **none** (`pg_constraint` → only the organization FK) ✓ |
| Index on `report_id` | **none** in migrations, in the dump (28 `CREATE INDEX` + 5 unique index statements exist, none for this table) or in the live DB (`pg_indexes` → only the PK) ✓ |
| Nullable | **yes** ✓ |
| Structurally prevents broader reuse | `VERIFIED` — a nullable, unconstrained uuid; a reused table would mean two different things selected by one column with **no discriminator** ✓ |
| Report-generation semantics | `VERIFIED` — the name, the design's `REFERENCES report_generation_queue(id)`, the report-section `prompt_type`, and the documented purpose all encode report provenance ✓ |

**OHD addition (`Cline finding` incomplete):** the design's `report_id` FK *is* declared in the repository — in `prisma/schema.prisma:620` (`report_generation_queue … @relation(fields: [report_id], …)`) — as are the two design indexes (`@@index([organization_id], map: "idx_ai_history_org")`, `@@index([report_id], map: "idx_ai_history_report")`). None of these exists in the SQL baseline, the dump or the live local database. Cline's statement that the design's FK/indexes "were not shipped" is correct for the SQL artefacts but is stated as a repository-wide absolute, which the Prisma declaration contradicts.

## 15. RLS / authorization verification

**Cline finding** — RLS is enabled on the table, **but no policy exists**, therefore `anon`/`authenticated` are denied by default and the table cannot be read by `authenticated` at all.

**OHD verified — `CONTRADICTED` (this is the most material discrepancy found in this verification).**

| Evidence | Finding |
|---|---|
| Phase 8 RLS enablement | `20260925000000_p8_rls_4b_group1_enablement.sql:80` lists `'ai_content_history'` in the approved 50-table array; header states `ENABLE ROW LEVEL SECURITY is idempotent, no policy or privilege is touched, no data is written` — **`VERIFIED`** |
| Root dump policies | **4 `CREATE POLICY` statements exist**: `CarbonTally_DB_Schema_V3M2.sql:4641` (DELETE), `:4645` (INSERT), `:4649` (SELECT), `:4653` (UPDATE), all `TO "authenticated"` |
| Policy semantics | SELECT allows `is_org_member(organization_id) OR is_org_consultant(organization_id)`; INSERT/UPDATE/DELETE allow `is_org_member(organization_id)`. **No creator-private predicate** (no `auth.uid()` term) |
| The cited migration's own guard | The enablement migration contains `SELECT count(*) INTO pol_count FROM pg_policies … ; IF pol_count = 0 THEN RAISE EXCEPTION 'RLS-4B guard: public.% has no policy; refusing to enable RLS (deny-all risk)…'`. Applied to an array that **includes this table**, the migration could not have completed if the table had no policy — i.e. the very migration Cline cites as proof of enablement attests to the **existence** of ≥1 policy |
| Live local Demo Lab DB (read-only) | `relrowsecurity = true`; `pg_policies` → **4 rows** (`ai_content_history_tenant_select/insert/update/delete`, `{authenticated}`), exactly matching the dump |

**Why Cline's search missed this:** the claim was derived from a **migrations-only** search using the pattern `ON public.ai_content_history` / `ON ai_content_history`. The policies live outside `supabase/migrations/` (in the root dump) and are written with quoted identifiers — `ON "public"."ai_content_history"` — which the unquoted pattern cannot match. The report's honest caveat ("the live database was not queried") does not rescue the conclusion, because the repository itself contained the disconfirming evidence.

**Practical consequence, verified as far as the evidence allows:**
* `anon`/`authenticated` are **not** deny-by-default on this table. RLS is enabled **and** four tenant-scoped policies are in force for `authenticated`, with INSERT/UPDATE/DELETE also permitted to organisation members.
* Any organisation member (and, for SELECT, any consultant with an active client grant per `is_org_consultant`) can therefore read and modify rows through the authenticated/PostgREST path. There is **no creator-private restriction**, which is inconsistent with the I2 visibility model (organisation **and** creator).
* `service_role` bypasses RLS on the platform's usual server-side posture — so a server-side path could read/write regardless.
* The derived architectural statement that "reuse requires policy design" **survives**, but its premise and character are wrong: the work is to **replace/tighten an existing permissive, non-creator-private, mutable policy set** — plus the granted INSERT/UPDATE/DELETE — not to create policies where none exist. Any later reuse must also reconcile with Master Spec §10 and I2's creator-private contract.
* **OHD cannot establish** the live policy state for any environment other than the local Demo Lab (production was not queried, by instruction).

## 16. Canonical Insight namespace verification

**Cline finding** — D2 R24/§3.2/§3.8 ratify `CarbonTally Insight / carbontally_insight_* / CarbonTallyInsight*` as the canonical technical/domain terminology for **new implementation**, superseding `ask_*`; a D3-era legacy-named table therefore sits outside the ratified namespace for new work.

**OHD verified** — **`VERIFIED`, with one nuance the report should carry.** D2 R24 (`…D2_PO_RATIFICATION_20260912.md:1470`) reads: "**CarbonTally Insight / `carbontally_insight_*` / `CarbonTallyInsight*` is the canonical technical/domain terminology for new implementation** … D1's `ask_*` proposal is **superseded for new implementation**; **no broad legacy rename required** | §3.2, §3.4.1, §3.8". D2 R1 (`:1447`) and §16-of-§3 (`:16`) corroborate. I1's tables are named `carbontally_insight_conversations` / `_messages`, consistent with the rule.

**Nuance (OHD):** the rule is scoped to **new implementation** and explicitly does **not** require renaming legacy structures. So the namespace argument supports "new I4 structures should live in the ratified namespace" and supports "reusing a legacy-named table for new work is inconsistent with the ratified terminology", but it does **not** by itself mandate renaming this table. Cline's report does not overstate this (it frames naming as a decision rather than a mandate) — this is a clarification, not a correction.

## 17. AI usage/cost-home verification

**Cline finding** — AI usage/cost already lives in other bounded locations: `report_generation_queue.ai_model_used/ai_tokens_used/ai_cost/ai_processing_time_ms`, `document_processing_queue` attribution fields, and `usage_tracking` aggregates; a "single bounded home" concern is real.

**OHD verified** — **`VERIFIED`.**

| Home | OHD verified content |
|---|---|
| `report_generation_queue` | `ai_model_used`, `ai_tokens_used`, `ai_cost`, `ai_processing_time_ms` — all four present (schema and live DB) ✓ |
| `document_processing_queue` | `automation_provider`, `automation_model`, `automation_model_version` (+ `automation_extracted_data`) — the truthful-attribution precedent, including a version column the legacy table lacks ✓ |
| `usage_tracking` | `id, organization_id, usage_date, usage_month, ai_files_processed, batch_files_uploaded, manual_pages_extracted, reports_generated, total_storage_bytes, created_at, updated_at` with **`UNIQUE (organization_id, usage_month)`** ✓ (aggregate/allowance layer, not per-generation) |

**Assessment of the "single-bounded-home" concern:** `VERIFIED` as an evidence statement — the platform already holds AI cost/usage in at least three bounded places (report generation, document processing, allowance aggregates), and Master Spec §23 forbids creating "a duplicate AI-history store" while requiring "one bounded home for AI interaction/cost/rating data". The concern Cline raises (a reused legacy table plus a new structure would add a fourth overlapping record) follows from verified facts, not from invention. This report does not redesign any of these systems and does not rank homes.

## 18. Audit separation verification

**Cline finding** — `public.audit_trail` is append/trigger protected; the current audit taxonomy has no AI category; `ai_content_history` is not and should not automatically be treated as the canonical audit ledger.

**OHD verified** — **`VERIFIED`.**

* `supabase/migrations/20260912000000_p7_audit_immutability_and_indexes.sql` defines `public.p7_audit_trail_immutable()` (raises for `UPDATE`/`DELETE`, `USING ERRCODE = 'raise_exception'`) and installs it as `BEFORE UPDATE OR DELETE ON public.audit_trail FOR EACH ROW`; its own comment states the canonical audit ledger is append-only "for every role" ✓.
* `backend/domain/audit.py` defines exactly the 12 categories Cline lists — `authentication, authorization, document, extraction, mapping, validation, calculation, evidence, workflow, report, administration, system` — with **no AI category** (grep for `AI_`/`ai_interaction`/`insight` in that module → 0) and `OUTCOMES = (success, failure)` ✓.
* Master Spec §20.4 (`:1037`) requires the AI audit event to "establish that the AI interaction occurred and **link to the durable interaction record**" and forbids placing "the entire AI transcript or provider payload into the canonical audit ledger unless separately authorized" ✓; §20.1 forbids collapsing the layers ✓.
* The legacy table has **no trigger** (`VERIFIED`, live DB: 0 non-internal triggers) and is mutable by policy — so it is not audit-grade, and Master Spec §8.2/§20.4 keep the ledger authoritative ✓.

## 19. Direct-reuse conclusion verification

**Cline finding** — "Direct reuse of the current table without restructuring is not appropriate."

**OHD verified — `VERIFIED` (supported), with one premise corrected.** Gap-by-gap:

| Gap asserted | OHD result |
|---|---|
| no Insight conversation parent | `VERIFIED` — absent from the DDL |
| no interaction parent (the decisive linkage) | `VERIFIED` — absent |
| no correlation ID | `VERIFIED` — absent |
| no lifecycle/status | `VERIFIED` — no status column, no trigger |
| provider/model-version structure insufficient | `VERIFIED` — `model_used` only; no provider, no version |
| no **appropriate** RLS policy | `PARTIALLY VERIFIED` — policies **exist** (4, verified in dump and live local DB) but are **not I2-consistent**: no creator-private predicate, and INSERT/UPDATE/DELETE granted to organisation members. The gap is "no appropriate policy", not "no policy" |
| no canonical Insight namespace | `VERIFIED` — D2 R24 scopes the canonical name to new implementation, with no broad rename required |
| report-generation-specific semantics | `VERIFIED` — `report_id`, `prompt_type` vocabulary, design purpose, Prisma `report_generation_queue` relation |
| no established I2 authorization model | `VERIFIED` — I2 requires organisation **and** creator (`insight_authz.py` `visibility_created_by`/`conversation_is_visible`); the table's policies carry no creator term |

**Conclusion:** using the table as-is could not satisfy Master Spec §9.3 (interaction reconstructability) or §10 (authorization/RLS consistency), and would require additive parents/discriminators plus a policy replacement anyway. The conclusion that **direct reuse without restructuring is inappropriate is supported by verified architecture and schema evidence**. The report's corollary that broader reuse remains *technically plausible* (nothing in the DDL forbids additive columns; `report_id` carries no shipped FK and is nullable) is also `VERIFIED`.

## 20. Separate-table architectural conclusion verification

**Cline finding** — a separately-scoped canonical Insight AI-generation table is architecturally cleaner than directly reusing the existing table, provided the single-bounded-home constraint is satisfied and the legacy table's disposition is decided at the same time.

**OHD verified — `SUPPORTED` as an architectural inference (`PARTIALLY VERIFIED` as a fact claim).**

Supporting verified facts: the ratified namespace exists for new implementation (D2 R24) and I1 is already named accordingly; any reuse must add the missing parent/discriminator columns anyway; a table with no creator-private predicate and with INSERT/UPDATE/DELETE granted to organisation members must have its policies replaced regardless; the legacy table's report-scoped semantics (`report_id`, `prompt_type`) would be overloaded; and Master Spec §23/§22.4 require exactly one bounded home while D2 §22.2 forbids automatic reuse or deletion and any migration *now*.

Why it is not a `VERIFIED` fact: it is an architectural judgement about cleanliness, not a proposition the repository can falsify. It is not the only defensible position — a restructured evolution of the legacy table is also contemplated by D2 §22.3 (Option B), and D2 §22.2's "no migration is authorised now" makes the deferral position (Option C) compliant too. This verification therefore records `SUPPORTED` for the reasoning and **ranks no option**.

**OHD note (boundary observation, not a violation):** the schema-fit report's §15–§18 present advantages/disadvantages per option and conclude that the separate structure is "architecturally cleaner", while explicitly labelling this `INFERENCE` and "not a PO decision". That is within an architectural-evidence remit; the wording nonetheless reads as a preference, so the PO should treat §18 as analysis input rather than as a recommendation.

## 21. Discrepancies / corrections to the Cline reports

| # | Severity | Report / location | Cline finding | OHD finding |
|---|---|---|---|---|
| D-1 | **MATERIAL** | Schema-fit §1.2, §2 (`:54`), §13, §19 (`:374`) | "**no RLS policy** … the table has **zero policies** → deny-by-default for `anon`/`authenticated`"; "cannot be read by `authenticated` at all" | **CONTRADICTED.** Four policies exist (`CarbonTally_DB_Schema_V3M2.sql:4641/4645/4649/4653`: SELECT/INSERT/UPDATE/DELETE to `authenticated`, org-scoped, SELECT also consultant-scoped, **no creator-private term**), and the live local Demo Lab DB has RLS enabled **with** those four policies. The Phase 8 enablement migration Cline cites contains a guard that **aborts** if any listed table has no policy. Consequence: the real posture is permissive and mutable, not deny-by-default; the "reuse needs policy design" claim survives but for the opposite reason (replace/tighten, not create) |
| D-2 | **MATERIAL** | Forensic §7 (`:156`), §9 (`:213`), §12 row 22; schema-fit §1.1 | "no ORM/model class ever existed" | **CONTRADICTED** for the ORM claim: `prisma/schema.prisma:599` declares `model ai_content_history` (+3 relations, +2 indexes), added in the same baseline commit `2d23fb8`; Prisma is a declared dependency of this repository. The weaker claim "no application reader/writer" remains `VERIFIED` |
| D-3 | Moderate | Forensic §4/§12 row 18; schema-fit §1.1, §2 | "0 `ALTER TABLE`, 0 `ADD COLUMN` across all refs" via `git log --all -S…` | **PARTIALLY VERIFIED.** Substance verified by direct inspection, but the cited command now returns **1** because the forensic report's own text introduces those strings (self-polluting method). Separately, the root dump contains `ALTER TABLE ONLY "public"."ai_content_history" ADD CONSTRAINT …` (quoted, line-wrapped) which the cited pattern cannot match |
| D-4 | Moderate | Forensic §9, §12 rows 21–23 | Current-tree reference inventory | **PARTIALLY VERIFIED.** Three omissions: `prisma/schema.prisma`; `CarbonTally_DB_Schema_V3M2.sql` (the artifact containing the policies Cline reported as absent); `e2e/environment/supabase/migrations/00000000000000_init_schema.sql:1041` (second DDL copy) |
| D-5 | Moderate | Schema-fit §1.2, §2, §12 (`:244`), §14 | "no index"; "no FK on `report_id`"; design indexes/FK "were not shipped" | **PARTIALLY VERIFIED.** True for the migrations, the root dump and the live local DB (PK index only; organization FK only). Not true repository-wide: `prisma/schema.prisma` declares both design indexes and the `report_generation_queue` relation on `report_id` |
| D-6 | Minor | Forensic §5 (`:52`-ish) / §12 row 9 | "16-column" citation attributed to `docs/ohd/reports/CT-P8X-DISCOVERY-…-002.md:47` | **CORRECTED.** `:47` is a table header; the `ai_content_history (16)` count is at **`:76`**. Substance unchanged |
| D-7 | Minor | Schema-fit §1.1/§8/§15 (`.3` citations) | "§15.3 requires provider **and** model **and** optional truthful `model_version`" | **PARTIALLY VERIFIED.** §15.3 requires distinguishing *configured* provider from *provider actually used*, and never claiming AI merely because a provider is configured; it does not mention `model_version` (0 occurrences in the Master Specification). The truthful-attribution principle is supported by §15.3 and §8.1 (`:436` "provider/model attribution when truthfully known"), and the `automation_model_version` precedent is real — but the specific requirement is not textual |
| D-8 | Minor (interpretation) | Schema-fit §5, §19 | "13 of 16 columns are non-report-specific" | **PARTIALLY VERIFIED.** Consistent with Cline's own matrix, but the defensible range is **12–14** depending on whether `prompt_type`/`content_format`/`prompt_text` are counted as report-flavoured. An interpretive aggregate, not a fact |
| D-9 | Informational | Both reports | Three schema declarations treated as one | The repository holds **three divergent declarations** of this table (SQL baseline; root dump; Prisma model) that disagree on varchar sizes, `Decimal(10,4)` vs `numeric`, `was_accepted` default, FKs and indexes. Cline analysed the SQL baseline only, which is the correct primary source for migrations but not the whole repository record |
| D-10 | Informational | Forensic §11; schema-fit §13 | "the live database was not queried" | Correct and honest; this verification additionally queried the **local Demo Lab** read-only, which confirms 0 rows, RLS enabled and 4 policies. Production remains unqueried |

**No discrepancy was found in:** the creation migration/lines/comment, the introducing commit and blame, the file's commit history, the original purpose quotations, the phase-association reasoning, the writer/reader absence, the "never altered (definition)" substance, the seed's data-stripped state, the AI usage/cost homes, the audit ledger's append-only trigger and taxonomy, the namespace rule, the I1/I2 disclaimers, the production-data limitation, and the scope discipline of both commits.

## 22. Evidence table (exact files / commits / lines)

| # | Evidence | Reference | Class |
|---|---|---|---|
| 1 | `CREATE TABLE public.ai_content_history ( … )` — 16 columns | `supabase/migrations/00000000000000_init_schema.sql:1041–1060` | OHD verified |
| 2 | `COMMENT ON TABLE … IS 'AI generation history'` | same, `:1060` | OHD verified |
| 3 | Section banner `-- PHASE D3 CONTINUED: AI CONTENT` | same, `:1038` (blame `dbe72aa6`, 2026-08-14) | OHD verified |
| 4 | All 20 creation lines blamed to `2d23fb89` | `git blame -L 1041,1060` | OHD verified |
| 5 | Introducing commit `2d23fb892921cbc41d6c0c20b7660e86fc968178`, `shomonrobie`, 2026-08-06 06:42:42 -0700, "CarbonTally RC2 Final database baseline" | `git log --diff-filter=A` on that file | OHD verified |
| 6 | File's 4-commit history (`eed55d6`, `2d23fb8`, `d3af816`, `dbe72aa`) | `git log --follow` | OHD verified |
| 7 | RC1 lineage (2026-08-04, `de94363`/`9f87229`) | `database/rc1/004_rc1_rls.sql:137` | OHD verified |
| 8 | Design artefact: purpose, `prompt_type` values, `report_id REFERENCES report_generation_queue`, `was_accepted DEFAULT TRUE`, `created_by REFERENCES organization_members`, 2 indexes | `docs/Final/UI_UX-Final_Guideline.md:495–531`, index `:958` (added in `2d23fb8`) | OHD verified |
| 9 | Legacy documentation of purpose | `docs/Final_Kimi/…/01_application_architecture.md:133`; `03_module_breakdown.md:277`; `04_api_design.md:247`; `CarbonTally_RC2_Architecture_Freeze.md:284` | OHD verified |
| 10 | "16" is a column count | `docs/ohd/reports/CT-P8X-DISCOVERY-…-002.md:76` (not `:47`) | OHD verified / corrected |
| 11 | No writer/reader ever: 0 for `INSERT`/`UPDATE`/`delete`/`FROM public…`/`AIContentHistory`/`aiContentHistory` once the two report commits are excluded; 1 `FROM ai_content_history` = QA command | `git log --all -S…` | OHD verified |
| 12 | No file named `*ai_content*` ever | `git log --all --name-only -- '*ai_content*'` → 0 | OHD verified |
| 13 | **No ORM claim contradicted**: `model ai_content_history` + 3 relations + 2 `@@index` | `prisma/schema.prisma:599–621`, back-relations `:2083/:2236/:2667`; dependency in root `package.json`; `seed.config.ts:13` | OHD verified (contradiction) |
| 14 | Never altered (substance): 0 `ALTER TABLE`/`ADD COLUMN`/`CREATE INDEX`/`idx_ai_history` for the table in any `.sql`; 0 non-internal triggers in live DB | whole-tree grep; live `pg_trigger` | OHD verified |
| 15 | Self-pollution of the cited `-S` counts | `git log --all -S'ALTER TABLE public.ai_content_history'` → 1 = commit `2c67a31` (the report) | OHD verified (correction) |
| 16 | `ALTER TABLE ONLY "public"."ai_content_history" ADD CONSTRAINT …` (quoted, wrapped) | `CarbonTally_DB_Schema_V3M2.sql:3243–3244`, `:4285–4286` | OHD verified |
| 17 | RLS enabled by Phase 8; header "no policy or privilege is touched" | `supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql:80` and header | OHD verified |
| 18 | **Four RLS policies for the table** (SELECT/INSERT/UPDATE/DELETE, `authenticated`, org-scoped, SELECT also consultant-scoped, no creator term) | `CarbonTally_DB_Schema_V3M2.sql:4641/4645/4649/4653` | OHD verified (contradicts "zero policies") |
| 19 | The cited migration's guard aborts if a listed table has no policy (`RAISE EXCEPTION 'RLS-4B guard: public.% has no policy; refusing to enable RLS (deny-all risk)'`) | same migration, guard block | OHD verified |
| 20 | Live local Demo Lab (read-only): 0 rows; `relrowsecurity = t`; 4 policies matching the dump; PK index only; organization FK only; 0 non-internal triggers | `carbontally_demo_local` `pg_class`/`pg_policies`/`pg_indexes`/`pg_constraint` | OHD verified |
| 21 | Seed is data-stripped: 134 `Data for Name:` headers, 0 `COPY` blocks | `supabase/seed.sql:181` | OHD verified |
| 22 | QA 0-row observation `[OBS]` and defect `QA-AI-001-D4` | `docs/verification/QA-AI-001-*.md:101, :202, :370, :392, :515, :560` | OHD verified |
| 23 | Feature audit "still dormant (0 rows, no application reference)" | `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md:200` | OHD verified |
| 24 | D2 §22.1–22.4: "Do NOT automatically reuse or delete it." / "No migration is authorised now." / Options A/B/C / single bounded home / AGENTS.md §66, §79 | `…D2_PO_RATIFICATION_20260912.md:1206–1232` | OHD verified |
| 25 | D2 R20; §27.2 open item | same `:1466`; `:1481` | OHD verified |
| 26 | D2 R24 canonical namespace (`carbontally_insight_*`), "no broad legacy rename required" | same `:1470` (also `:1447`, `:16`) | OHD verified |
| 27 | Master Spec §23: do not automatically reuse/delete; **one bounded home for AI interaction/cost/rating data** | `docs/architecture/CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md:1090–1100` | OHD verified |
| 28 | Master Spec §9.3 reconstruction chain; §15.4 `tokens_used = NULL`/`cost = NULL`; §20.4 link-to-record + no payload; §20.1 no layer collapse; §8.1 `:436` "provider/model attribution when truthfully known"; §41 `:1890` "raw question storage versus hash"; `model_version` → 0 occurrences | same document (`:506`, `:815`, `:1037`, `:1009/1011`, `:436`, `:1890`) | OHD verified (with D-7) |
| 29 | I4 pre-authorization audit: no application references (FACT `:341`); disposition `UNRESOLVED` (`:351`); cites Spec §23 L1090–1100 | `docs/implementation/phase8/CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921.md` | OHD verified |
| 30 | I1/I2 disclaim the table | `20261001000000_…:24`; `20261002000000_…:28`; tests `test_i1_insight_migration.py:17,134`; `test_i2_insight_authorization_contracts.py:111` | OHD verified |
| 31 | AI usage/cost homes: `report_generation_queue.ai_model_used/ai_tokens_used/ai_cost/ai_processing_time_ms`; `document_processing_queue.automation_provider/automation_model/automation_model_version`; `usage_tracking` with `UNIQUE (organization_id, usage_month)` | schema + live DB (`information_schema`, `pg_constraint`) | OHD verified |
| 32 | Audit ledger append-only: `p7_audit_trail_immutable()` trigger `BEFORE UPDATE OR DELETE` "for every role"; taxonomy 12 categories, no AI; outcomes success/failure | `supabase/migrations/20260912000000_…sql:32–49`; `backend/domain/audit.py:23–61` | OHD verified |
| 33 | Both analysed commits are documentation-only (1 file each: 367 / 409 insertions); I4 audit commit likewise | `git diff --name-only 2c67a31^ 123cc3a -- . ':!docs/**'` → empty | OHD verified |
| 34 | Production row presence; external writers; original V1/V2 authoring; live policy state outside the local demo DB; whether the Prisma-declared indexes/FKs exist in any live environment | no repository artefact; production not queried | **OHD cannot establish** |

## 23. Final independent verification verdict

| # | Finding under verification | Classification |
|---|---|---|
| 1 | Creation migration, lines 1041–1060, 16 columns, comment `'AI generation history'` | **VERIFIED** |
| 2 | Introducing commit `2d23fb892921cbc41d6c0c20b7660e86fc968178` + blame + 4-commit file history | **VERIFIED** |
| 3 | Original purpose ("Track AI-generated content with feedback"; report-generation scoped) | **VERIFIED** (one citation line corrected) |
| 4 | No application code has ever read or written the table | **VERIFIED** |
| 5 | "No ORM/model class ever existed" | **CONTRADICTED** (Prisma model in the same baseline commit) |
| 6 | Never altered (no column change), never dropped/renamed, no trigger, no index, no `report_id` FK | **VERIFIED** for the SQL baseline, dump and live local DB; **PARTIALLY VERIFIED** repository-wide (Prisma declares the indexes and FK) |
| 7 | Phase association: RC2-baseline legacy, predating Phase 8, none of Phase 1–7; banner is a schema-build section | **VERIFIED** |
| 8 | Current usage: no runtime path; repository references limited to schema/comments/tests/docs | **VERIFIED** (inventory had 3 omissions) |
| 9 | `PRODUCTION ROW PRESENCE NOT VERIFIED`; local demo 0 rows | **VERIFIED** |
| 10 | Per-column schema-fit classifications | **VERIFIED** individually |
| 11 | "13 of 16 columns non-report-specific" | **PARTIALLY VERIFIED** (interpretive; range 12–14) |
| 12 | `report_id`: nullable, no FK, no index, report-centric, does not structurally block reuse | **VERIFIED** (SQL/dump/live DB), with the Prisma divergence noted |
| 13 | RLS enabled **but zero policies** → deny-by-default for `authenticated` | **CONTRADICTED** (4 policies exist; live DB confirms; the cited migration's guard presupposes them) |
| 14 | Canonical Insight namespace ratified for new implementation | **VERIFIED** |
| 15 | AI usage/cost already bounded elsewhere; "single bounded home" concern is real | **VERIFIED** |
| 16 | Canonical audit ledger separation; taxonomy has no AI category; the legacy table is not audit-grade | **VERIFIED** |
| 17 | "Direct reuse of the current table without restructuring is not appropriate" | **VERIFIED** (one premise corrected: no *appropriate* policy, not *no* policy) |
| 18 | "A separate, canonically-named Insight AI-generation record is architecturally cleaner" | **SUPPORTED** as architectural inference (`PARTIALLY VERIFIED` as a fact claim); no option ranked |
| 19 | Boundary discipline (Layer 1, audit ledger, retention, billing, context, RAG, status taxonomy, migration, retirement, production ops kept outside the task) | **VERIFIED** — no boundary violation found |
| 20 | Original V1/V2 authorship; production rows; external writers; live policy/FK/index state outside the local demo DB | **UNKNOWN / NOT REPOSITORY-VERIFIABLE** |

**Overall independent verification result.**

* **Cline's historical findings are independently supported**, with two corrections that do not change the forensic narrative: the "no ORM model" claim is contradicted (D-2), and the alteration/usage search counts are self-polluted and pattern-limited (D-3), though their substance holds under direct inspection. Creation, provenance, purpose, non-use, non-alteration, phase association and the production-data limitation all reproduce exactly.
* **Cline's schema-fit findings are largely supported, but one load-bearing technical claim is wrong.** The column matrix, the missing Insight discriminators, the report-specific semantics, the namespace argument, the AI-home duplication concern and the audit separation all verify. The claim that the table has **zero RLS policies and is deny-by-default for `authenticated`** is **CONTRADICTED** by three independent sources — including a policy set that makes the table readable *and writable* by organisation members with no creator-private restriction. This makes the table's current posture **more** permissive than the report states, and changes the nature (not the existence) of the policy work any later disposition would require.
* **Is "direct reuse is inappropriate" adequately supported?** **Yes.** The verified gaps — no conversation/interaction parent, no correlation identifier, no lifecycle status, no provider or model version, no creator-private authorization consistent with I2, report-generation-specific semantics, and a namespace ratified for new implementation — independently establish that the table as-is could not satisfy the interaction-reconstructability and authorization-consistency requirements, and that additive restructuring plus policy replacement would be required regardless. The conclusion stands on corrected premises.
* **Separate-structure reasoning** is `SUPPORTED` as an architectural inference; this verification ranks no option and selects no disposition.

**No overall "PASS" is issued for the Cline reports as a body of work**, because one material schema-fit claim is contradicted; the correct characterisation is: **historical findings verified with corrections; schema-fit findings verified except the RLS-policy premise, which is contradicted.**

## 24. Explicit PO decisions that remain open

Nothing below was decided, changed, implemented or recommended by this verification:

1. **Q1** — the bounded home for AI interaction/cost/rating data (D2 §22.3 Options A/B/C): **OPEN**. This report does not resolve it, does not approve reuse, does not approve deletion and does not approve migration.
2. Whether the legacy table is retained as-is, restructured/evolved, formally retired, or superseded: **OPEN**; any of these needs an authorised disposition (D2 §22.2 currently forbids automatic reuse or deletion and authorises no migration).
3. Whether any RLS policy set for the legacy table or for a successor should be replaced, tightened or re-designed to be I2-consistent (creator-private): **OPEN** — and now known to require *replacement of an existing permissive policy set*, not first-time policy creation.
4. Whether the **Prisma schema's divergent declaration** of this table (indexes, `report_id`/`created_by` relations, varchar sizes, `was_accepted` default) should be reconciled with the SQL baseline, and which declaration is authoritative: **OPEN** (raised by this verification; D-9).
5. **Q2** — canonical ledger for AI audit events: **OPEN**.
6. **Q3** — answer-status enumeration versus I3's closed vocabulary: **OPEN**.
7. **Q4 / §41 PR-EX3** — raw prompt/question storage versus hash: **OPEN**.
8. **Q5** — Layer-2 mutability/immutability posture: **OPEN**.
9. **Q7** — Layer-1 lifecycle status: **OPEN**.
10. **I7** — retention, deletion, export, residency, provider retention: **DEFERRED**, not invented here.
11. **I8** — billing, credits, allowances, provider cost policy: **DEFERRED**.
12. An authorised read-only **production** row-presence check, an external-writer assessment, and a live policy/privilege inventory per environment: **NOT PERFORMED** here (production was not queried by instruction).
13. End-user feedback/rating/acceptance as an Insight product feature: **OPEN** (no ratified requirement found).
14. **I4 authorization** and any implementation, migration, rename, backfill or data handling: **NOT AUTHORIZED** and untouched by this task.

**This is an independent verification result only. Q1 remains a PO decision. I4 remains NOT AUTHORIZED. No disposition of `ai_content_history` is proposed, approved or performed.**
