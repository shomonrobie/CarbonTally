# CT-P8-I4-AI-CONTENT-HISTORY-ORIGIN-FORENSIC-20260921

**Task:** read-only historical forensic investigation into the origin, purpose and current standing of `public.ai_content_history`.
**Checkout:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Starting HEAD:** `fca54696009ada88a65267dc90c8a5f092f3c20a`
**Scope discipline:** no application code, migration, schema, test, configuration or other document was modified; no database (local, demo or production) was queried; no destructive command was run; nothing was implemented; Q1 was **not** decided.
**Labels:** `DIRECT` = stated by a repository artefact; `INFERENCE` = reasoned from evidence; `UNKNOWN` = not established by repository evidence.

---

## 1. Executive conclusion

`DIRECT` — `public.ai_content_history` is a **legacy pre-Phase-8 AI-content journal** carried into the CarbonTally V3 baseline from the earlier (RC1/RC2, V1/V2-era) database design. It was never created by a Phase 1–8 migration: it enters this repository inside the monolithic V3 initial schema (`supabase/migrations/00000000000000_init_schema.sql`, lines 1041–1060), committed as the "CarbonTally RC2 Final database baseline" on 2026-08-06.

`DIRECT` — its documented purpose is to **track AI-generated report content together with its prompt, model, generation metrics and human feedback**: the original design artefact states verbatim `-- TABLE: ai_content_history` / `-- Purpose: Track AI-generated content with feedback`, with `prompt_type` examples `'executive_summary', 'analysis', 'methodology'` and a foreign key to `report_generation_queue(id)`.

`DIRECT` — **no application code in this repository has ever read or written it**: `git log --all -S'AIContentHistory'` → 0 commits; `-S'aiContentHistory'` → 0 commits; no file whose name contains `ai_content` has ever existed; the only current-tree mentions are two Insight tests (asserting the I1/I2 migrations do **not** touch it), two Phase 8 analysis documents, and the RLS-enablement array.

`DIRECT` — the table has **never been altered**: across all refs, `git log --all -S'ALTER TABLE public.ai_content_history'` → 0 and `-S'ai_content_history ADD COLUMN'` → 0. Its only later structural interaction is inclusion in the Phase 8 bounded RLS-enablement array, whose own header states it enables RLS and "touches no policy or privilege".

`DIRECT` — the RC2 Architecture Freeze decision record lists `ai_content_history | — all columns | KEEP` under "2.13 Reports & AI content", i.e. it was **retained**, not deprecated; the Phase 8 discovery later flagged it as a **dormant asset with zero code references** and "a partial precedent for AI cost/rating storage"; the D2 ratification and Master Specification v1.1 §23 then placed its disposition in the **open** I3/I4 decision space ("select one bounded home for AI interaction/cost/rating data"), forbidding automatic reuse, automatic deletion or a duplicate AI-history store.

`INFERENCE` — it is therefore best described as a **report-generation-era AI journal whose original producer no longer exists in this codebase**, with an intent (AI usage/cost/rating telemetry) that is partly superseded by `report_generation_queue.ai_model_used/ai_tokens_used/ai_cost` and partly a live candidate in the I4 bounded-home decision.

`UNKNOWN` — whether any environment (production, demo, local) holds rows in it. Documented evidence is environment-specific (§11), so this report records `PRODUCTION ROW PRESENCE NOT VERIFIED`.

---

## 2. Exact creation migration

| Item | Value | Evidence class |
| --- | --- | --- |
| Migration file | `supabase/migrations/00000000000000_init_schema.sql` | `DIRECT` |
| Version/timestamp prefix | `00000000000000` (V3 initial/baseline schema, deliberately unordered) | `DIRECT` |
| Creation lines | 1041–1060 (`CREATE TABLE public.ai_content_history ( … );`, comment at 1060) | `DIRECT` (`git blame -L 1036,1062`) |
| Section banner | line 1038 `-- PHASE D3 CONTINUED: AI CONTENT` | `DIRECT` |
| Banner provenance | the banner alone is blamed to `dbe72aa6` (2026-08-14); the `CREATE TABLE` lines are **not** | `DIRECT` |
| Altered since creation? | **No** — 0 `ALTER TABLE`, 0 `ADD COLUMN` occurrences across all refs | `DIRECT` |
| Named by later migrations? | Once: `20260925000000_p8_rls_4b_group1_enablement.sql:56` (RLS-enable array; "ENABLE ROW LEVEL SECURITY is idempotent, no policy or privilege is touched") | `DIRECT` |
| Also referenced by | `database/rc1/004_rc1_rls.sql:137` (RC1 bundle, committed 2026-08-04 — **earlier** than the baseline) | `DIRECT` |

`INFERENCE` — because the RC1 RLS bundle already enumerates `ai_content_history` two days before the RC2 baseline commit, its true origin predates this repository's baseline: it belonged to the pre-V3 CarbonTally database that the V3 schema baseline was reconciled from.

---

## 3. Exact introducing commit

| Item | Value |
| --- | --- |
| Commit | `2d23fb892921cbc41d6c0c20b7660e86fc968178` (`2d23fb8`) |
| Subject | `CarbonTally RC2 Final database baseline` |
| Author | `shomonrobie <38324907+shomonrobie@users.noreply.github.com>` |
| Author date | `Thu Aug 6 06:42:42 2026 -0700` (2026-08-06) |
| Creation method | `git log --diff-filter=A --format=… -- supabase/migrations/00000000000000_init_schema.sql` |
| Blame confirmation | every line 1041–1060 attributed to `2d23fb89` |

`DIRECT` — related history for the same file: `git log --follow` shows 4 commits — `eed55d6` and `2d23fb8` ("CarbonTally RC2 Final database baseline", 2026-08-06) and `d3af816` and `dbe72aa` ("checkpoint: verified V2.1 and V3 database foundation", 2026-08-14). The later pair re-organised/annotated the file (source of the `PHASE D3 CONTINUED: AI CONTENT` banner) but did not touch the table's definition.
`UNKNOWN` — the commit that originally authored the table in the pre-baseline database is not present in this repository's history (the RC1 bundle `database/rc1/**` references it but does not create it).
---

## 4. Original schema (as introduced; unchanged to this day)

`DIRECT` — `supabase/migrations/00000000000000_init_schema.sql:1041–1060` (all lines blamed to `2d23fb89`):

```sql
CREATE TABLE public.ai_content_history (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    report_id UUID,
    prompt_type VARCHAR NOT NULL,
    prompt_text TEXT,
    model_used VARCHAR,
    generated_content TEXT,
    content_format VARCHAR,
    tokens_used INTEGER CHECK (tokens_used IS NULL OR tokens_used >= 0),
    processing_time_ms INTEGER CHECK (processing_time_ms IS NULL OR processing_time_ms >= 0),
    cost NUMERIC CHECK (cost IS NULL OR cost >= 0),
    user_rating INTEGER CHECK (user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5)),
    user_feedback TEXT,
    was_accepted BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);
COMMENT ON TABLE public.ai_content_history IS 'AI generation history';
```

`DIRECT` — 16 columns; `docs/cline/CarbonTally_DB_Schema_V3M2.md:1063–1088` documents exactly this column set (`int4`/`numeric`/`bool`) with the same comment, and `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md:47` records it as a **16-column** table — i.e. "16" is a column count, not a row count (the same sentence counts `document_processing_queue` as "79 cols").

`DIRECT` — the retained design artefact differs only in detail: it declared `report_id … REFERENCES report_generation_queue(id)`, sized varchars (`prompt_type VARCHAR(50)`, `model_used VARCHAR(50)`, `content_format VARCHAR(20)`), `cost DECIMAL(10,4)`, `was_accepted BOOLEAN DEFAULT TRUE`, `created_by … REFERENCES organization_members(id)` and two indexes (`idx_ai_history_org(organization_id)`, `idx_ai_history_report(report_id)`). The shipped baseline dropped the two inline FKs and the two indexes and added CHECK constraints — a normalised re-expression of the same design.
---

## 5. Historical purpose

`DIRECT` — the strongest evidence is the original design document retained in this repository, `docs/Final/UI_UX-Final_Guideline.md:495–531` (added in the same RC2 baseline commit `2d23fb8`), whose index entry at `:958` reads `ai_content_history — Track AI-generated content`:

```sql
-- ============================================
-- TABLE: ai_content_history
-- Purpose: Track AI-generated content with feedback
-- ============================================

CREATE TABLE ai_content_history (
    ...
    report_id UUID REFERENCES report_generation_queue(id),
    prompt_type VARCHAR(50) NOT NULL, -- 'executive_summary', 'analysis', 'methodology'
    model_used VARCHAR(50),
    generated_content TEXT,
    content_format VARCHAR(20), -- 'text', 'markdown', 'html'
    -- Metrics
    tokens_used INTEGER, processing_time_ms INTEGER, cost DECIMAL(10,4),
    -- Feedback
    user_rating INTEGER, -- 1-5
    user_feedback TEXT, was_accepted BOOLEAN DEFAULT TRUE,
);
CREATE INDEX idx_ai_history_org ON ai_content_history(organization_id);
CREATE INDEX idx_ai_history_report ON ai_content_history(report_id);
```

`DIRECT` — corroborating statements in the retained legacy architecture/audit set (also added at commit `2d23fb8`):

* `docs/Final_Kimi/Kimi_Agent_UK_IE_Compliance_Audit_Report/01_application_architecture.md:133` — "**History**: AI interactions are journaled in `ai_content_history` for auditability and prompt/version traceability."
* same file `:280` — the AI extraction flow records field/mapping hints in `extracted_data` jsonb with "`ai_content_history` journaled".
* `…/03_module_breakdown.md:277` — `| ai_content_history | Prompt/response audit |`.
* `…/04_api_design.md:247` — endpoint 71 `GET /audit/reports/{reportId}` (viewer+) returns `report_versions` history plus "`ai_content_history` provenance (model, tokens, cost)".
* `…/carbontally_uk_ie_review_sec03.md:112` — rating coverage: `ai_content_history.user_rating` "CHECK 1–5".
* `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md:106` — "**AI usage + cost already captured** — `ai_content_history` (tokens, cost, model, latency), plus `ai_*` fields on the processing queue and report queue."

**Purpose, stated without inference:** the table was the **journal of AI-generated content** — the prompt issued to a model, the model used, the generated content and its format, generation metrics (tokens, latency, cost) and the human response to it (1–5 rating, free-text feedback, acceptance flag) — scoped to an organisation and optionally to a report, serving auditability, prompt/version traceability and a per-report AI-provenance view. The report-generation reading rests directly on the `prompt_type` enumeration (`executive_summary`, `analysis`, `methodology`) and the `report_id` link to `report_generation_queue`.
---

## 6. Phase association

`DIRECT` — the table sits under the banner `-- PHASE D3 CONTINUED: AI CONTENT` in `init_schema.sql`, alongside `PHASE D1: FOUNDATION & EXTENSIONS` (:9), `PHASE D2: CORE BUSINESS TABLES` (:182), `PHASE D3: TRANSACTIONAL TABLES` (:614), `PHASE D3 CONTINUED: PROCESSING & QUEUE` (:777), `PHASE D3 CONTINUED: REPORTS` (:944), `PHASE D4: SUPPORTING TABLES` (:1063), `PHASE D4 CONTINUED: LOGS & AUDIT` (:1644) and `PHASE D5: CONSTRAINTS & INDEXES` (:2133).

`DIRECT` — those banners are **schema-construction sections of the V3 database baseline** (D1 foundation → D2 core business → D3 transactional → D4 supporting/logs → D5 constraints); they are not the programme's product phase numbering, and the banner itself was added on 2026-08-14 (`dbe72aa6`), eight days after the table was committed.

`DIRECT` — timeline establishing the phase boundary:

| Date | Commit(s) | Event |
| --- | --- | --- |
| 2026-08-04 | `de94363`, `9f87229` | `rc1 database full` — RC1 SQL bundle; `database/rc1/004_rc1_rls.sql:137` already enumerates `ai_content_history` |
| 2026-08-06 | `2d23fb8`, `eed55d6` | `CarbonTally RC2 Final database baseline` — **creates the table** in `00000000000000_init_schema.sql` |
| 2026-08-14 | `dbe72aa`, `d3af816` | `checkpoint: verified V2.1 and V3 database foundation` — adds the `PHASE D3 CONTINUED: AI CONTENT` banner |
| 2026-09-15 | `1db97ba` | `fix(security): enable bounded RLS coverage` — lists the table in the RLS-enable array |
| 2026-09-21 | `5633798`, `de18c35`, `6e4b5a1`, `66adfb5`, … | Phase 8 I1/I2 — mention it only in comments/tests, asserting it is not touched |

**Answer:** `DIRECT` — **no evidence associates the table with product Phase 1, 2, 3, 4, 5, 6 or 7**, and it is **not a Phase 8 creation either**: it predates Phase 8 by roughly five weeks and was inherited from the legacy RC1/RC2 database into the V3 baseline. The only phase-like label the evidence supports is the V3 **schema-build section "PHASE D3 (AI CONTENT)"**, which is not a product phase.
`UNKNOWN` — whether the original authorship belonged to a V1 or a V2 development phase; no artefact in this repository dates the original authoring, because the pre-baseline database history is not in this repository.
---

## 7. Historical application references

`DIRECT` — searches over **all refs** (`git log --all -S…`, whole repository, not just the working tree):

| Search pattern | Commits | Interpretation |
| --- | --- | --- |
| `AIContentHistory` | **0** | no class/type of that name ever existed |
| `aiContentHistory` | **0** | no camelCase ORM/identifier ever existed |
| `ai_content_history` | 24 | see grouping below |
| `INSERT INTO public.ai_content_history` | **0** | no writer ever existed |
| `INSERT INTO ai_content_history` | **0** | no writer ever existed |
| `UPDATE public.ai_content_history` | **0** | no updater ever existed |
| `ai_content_history SET` | **0** | no write statement |
| `delete from ai_content_history` | **0** | no deleter ever existed |
| `FROM public.ai_content_history` | **0** | no qualified reader |
| `FROM ai_content_history` | **1** | a Phase 8 **QA command**, not application code |
| files ever named `*ai_content*` | **0** | no module, repository, service, route or fixture was ever dedicated to it |

`DIRECT` — the 24 commits that introduce or change the string fall into three groups, none of which is application code:

1. **Legacy baselines/dumps:** `de94363`, `9f87229` (rc1 database full, 2026-08-04); `2d23fb8`, `eed55d6` (RC2 Final database baseline, 2026-08-06 — the creation); `38ae49e`, `cfabe26` (V3 baseline checkpoints); `077c866` (finalize v3 ux); `daad396` (production release 1).
2. **Security hardening:** `1db97ba` (`fix(security): enable bounded RLS coverage`) — adds the table to the RLS-enablement array.
3. **Phase 8 documentation and Insight stage work:** `8608d13` (Ask persistence discovery), `0f522e2` (QA-AI-001), `f671ec3`, `2a34557`, `e48ee55`, `5bd5e29` (feature audit), `5633798` (I1 code — comment only), `6e4b5a1`, `66adfb5`, `de18c35` (I2 code — comment only), `ad49f57`, `682d591`, `fca5469`.

`DIRECT` — ancillary artefacts that mention it: `tools/carbon_data_factory/schema.txt:1041,1060` (a copy of the DDL used as schema text by a data-factory tool; no generator code references the table) and `supabase/seed.sql:181`, which contains **only** the pg_dump-style header comment `-- Data for Name: ai_content_history; Type: TABLE DATA; Schema: public; Owner: postgres` with **no `COPY`/data block** — the same pattern appears for every table in that file, including `organizations`, so the seed is **data-stripped** and neither seeds nor populates any table.

**Historical usage conclusion:** `DIRECT` — **no application code in this repository has ever written to or read from `public.ai_content_history`.** The only reader ever recorded is a read-only QA measurement command (`SELECT count(*) FROM ai_content_history`, `docs/verification/QA-AI-001-…:515`). `INFERENCE` — the legacy journaling described in §5 was performed by pre-V3 application code that is not part of this repository's history; the table was carried forward for schema continuity, not for continuing use.

---

## 8. Removal / replacement history

`DIRECT` — **no removal**: the `CREATE TABLE` definition committed at `2d23fb8` is still the definition at HEAD, and no commit in the reachable history records a drop. `DIRECT` — **no structural replacement**: no `ALTER TABLE`, no `ADD COLUMN` (`0` hits for both patterns across all refs) and no later migration recreates or supersedes the table.

`DIRECT` — **partial functional replacement**, evidenced by the RC2 Architecture Freeze decision record: AI telemetry for report generation is also carried by `report_generation_queue`, whose `ai_model_used`, `ai_tokens_used` and `ai_cost` columns are described there as "the committed FinOps surface" (`docs/Final_Kimi/…/CarbonTally_RC2_Architecture_Freeze.md`, section 2.13 "Reports & AI content (5 tables)"), and which the OHD operational-intelligence discovery lists separately from `ai_content_history` (`CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md:79–80`). `INFERENCE` — the cost/usage role originally assigned to `ai_content_history` was in practice assumed by the report/processing queues' `ai_*` columns, which are the columns that the platform's own FinOps documentation treats as authoritative.

`DIRECT` — later architectural decisions found:

* **RC2 Architecture Freeze:** `ai_content_history | — all columns | KEEP` under "2.13 Reports & AI content" — a **retention** decision (no deprecation language found).
* **D2 PO Ratification §22 (2026-09-12):** §22.2 "**Do NOT automatically reuse or delete it.** **No migration is authorised now.**"; §22.3 records three options for a later repository-driven decision — **Option A** the new Insight interaction domain (Layer 2), **Option B** an extension of the existing AI table, **Option C** another bounded structure; §22.4 requires a single bounded home and forbids duplicate AI-history stores.
* **D2 R20 / §27.2:** "Dormant AI structure — Not reused or deleted; repository-driven decision recorded for I3/I4; no migration now", and the open item "dormant AI structure home (option A/B/C) — Repository-driven · I3/I4".
* **Master Specification v1.1 §23:** "The repository contains a dormant AI-related data structure identified during discovery… The I3/I4 repository-driven decision must select one bounded home for AI interaction/cost/rating data."
* **QA-AI-001 (Phase 8):** defect record `QA-AI-001-D4` (Informational) — "`ai_content_history` remains dormant (0 rows, unreferenced by code) pending the D2 §22 decision (Option A/B/C) at I4. No action is authorised now."

`INFERENCE` — no historical documentation states that the table was **deprecated**, replaced, or formally retired; no statement reserves it for backward compatibility either. Its status throughout Phase 8 is "**dormant, deliberately untouched, decision deferred to I4**".
---

## 9. Current application references

`DIRECT` — a full current-tree grep (`grep -rn 'ai_content_history' .` excluding `.git`) returns exactly these, and **no runtime application path among them**:

| Reference | Path:line | Nature |
| --- | --- | --- |
| DDL creation + comment | `supabase/migrations/00000000000000_init_schema.sql:1041,1060` | schema definition (creation) |
| RLS enablement list | `supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql:80` | Phase 8 security hardening — named in the approved table array so RLS is enabled; the migration states it touches no policy or privilege and writes no data |
| I1 non-scope comment | `supabase/migrations/20261001000000_p8_i1_insight_persistence.sql:24` | "is NOT reused, migrated, altered or deleted" |
| I2 non-scope comment | `supabase/migrations/20261002000000_p8_i2_insight_authorization.sql:28` | records that I2 performs no alteration of it |
| I1 test assertion | `backend/tests/unit/data/test_i1_insight_migration.py:17,134` | asserts the I1 DDL does **not** contain the table |
| I2 test assertion | `backend/tests/unit/data/test_i2_insight_authorization_contracts.py:111` | asserts the I2 migration does **not** touch it (grouped with human messaging) |
| Seed dump header (empty) | `supabase/seed.sql:181` | pg_dump-style header only; no data block |
| Data-factory schema text | `tools/carbon_data_factory/schema.txt:1041,1060` | verbatim DDL copy; no generator code references it |
| Analysis/documentation | `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md:200,1049`; `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md:47,106`; `docs/verification/QA-AI-001-…:101,202,370,392,515,560`; `docs/cline/CarbonTally_DB_Schema_V3M2.md:1063`; `docs/cline/prompt-history/CT-P8-ASK-CARBONTALLY-PERSISTENCE-DISCOVERY-20260912-013.md:85`; `docs/cline/reports/CT-P8-CURRENT-STATE-RECOVERY-20260913-023.md:276`; `docs/Final/**`, `docs/Final_Kimi/**` | documentation and evidence only |

`DIRECT` — there is **no** `backend/data/*` repository, `backend/services/*` service, `backend/api/*` route, frontend module, job, worker or fixture for the table, and no ORM/model class ever existed (§7).

---

## 10. Relationship to the current Phase 8 Insight architecture

| Dimension | `ai_content_history` (legacy) | Insight I1 Layer 1 (`carbontally_insight_conversations` / `_messages`) | Proposed I4 Layer 2 (per Master Spec §8.1/§9.3) | Layer 3 (`public.audit_trail`) |
| --- | --- | --- | --- | --- |
| Domain | report-generation AI content journal (legacy) | conversational Insight | AI interaction execution record | platform canonical audit ledger |
| Conversation/message linkage | none (only optional `report_id`) | conversation id + 1-based `ordinal` | conversation + message link specified | none (generic `table_name`/`record_id`) |
| Actor | `created_by UUID` **nullable**, no RLS creator predicate of its own | `created_by NOT NULL` + creator-private RLS | actor required by §9.3 | `performed_by NOT NULL` |
| Organisation | `organization_id NOT NULL` + `ON DELETE CASCADE` | same pattern | required by §9.4 | via `metadata->>'organization_id'` (queryable today) |
| Intent / tool invocation / references / answer status | absent (has `prompt_type` only) | absent | specified (not yet designed) | absent by design (§20.4 forbids payload dumps) |
| Provider/model | `model_used` only (no provider, no model_version) | n/a | provider/model "when truthfully known" (§15.3) | n/a |
| Usage/cost | `tokens_used`, `cost`, `processing_time_ms` (nullable, CHECK ≥ 0) | n/a | "where truthfully available" — must be NULL today because `ChatCompletionResponse` exposes no usage | n/a |
| Human feedback | `user_rating` (1–5), `user_feedback`, `was_accepted` — a capability **no** ratified Insight layer currently specifies | absent | not specified by the spec text | absent |
| Content | `prompt_text`, `generated_content`, `content_format` | `content text` | question/answer/context | excluded by §20.4 |
| Immutability | none (no trigger; RLS enabled Phase 8) | select/insert for authenticated; no update/delete in I1 | not yet decided (§8.2 "separate lifecycle") | append-only + trigger-immutable |
| Layer collapse | single table mixes content + telemetry + feedback, contrary to §20.1 "These must not be collapsed" | Layer 1 only | Layer 2 | Layer 3 |

`DIRECT` — I1 and I2 explicitly disclaimed it (migration comments and tests), I3 has no persistence at all, and the I4 read-only pre-authorization audit (`CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921.md`, §16) recorded its disposition as `UNRESOLVED` and tied it to Q1.
`INFERENCE` — the table is **not** a Layer-1 artefact, **not** the Layer-3 ledger, and **not** a drop-in Layer-2 record: it lacks every Layer-2 discriminator except content/telemetry, while carrying two capabilities (rating/feedback/acceptance) that the ratified Insight layers do not currently specify. The only genuine intersection with I4's requirements is AI **usage/cost/rating** storage — exactly the subject of D2 §22 and Q1.
---

## 11. Production-data evidence limitations

`DIRECT` — what repository evidence **does** establish:

* **No writer exists.** Zero `INSERT`/`UPDATE`/`DELETE` statements against the table in any commit (§7); no repository/service/route/fixture for it in the current tree (§9).
* **No migration seeds it.** `supabase/seed.sql:181` contains only the pg_dump-style header comment with **no data block** — and the same holds for every table in that file, so the seed is data-stripped.
* **No test populates it.** The only test mentions are negative assertions (`test_i1_insight_migration.py`, `test_i2_insight_authorization_contracts.py`).
* **Measured empty in one environment:** `docs/verification/QA-AI-001-…md` reports, evidence-classed `[OBS]`, "`ai_content_history` — 0 rows", measured by `SELECT count(*) FROM ai_content_history` (`:515`, `:370`) against the **local demo database** `carbontally_demo_local`, read-only; the Phase 8 feature audit repeats "`ai_content_history` still dormant (0 rows, no application reference)" (`docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md:200`).
* **Phase 8 touched its security posture:** RLS was enabled on it (`1db97ba`, migration `20260925000000`), whose header states no policy or privilege was touched.

`DIRECT` — what repository evidence does **not** establish:

* whether **production** holds rows;
* whether any legacy or external system outside this repository still writes to it;
* whether manual / Studio / SQL-console operations have populated it;
* whether any RLS **policy** (as opposed to RLS being enabled) exists on it — no policy definition for this table was found in the inspected migrations.

**Statement required by this investigation:**

`PRODUCTION ROW PRESENCE NOT VERIFIED`

`INFERENCE` — the absence of an application writer plus a single read-only observation of 0 rows in the local demo environment makes a non-zero production population **unlikely**, but that is not proof, and it must not be inferred from the absence of code references. Any decision that depends on the table being empty (or on its contents being disposable) requires an authorised, read-only production count that this task neither performed nor was permitted to perform.
---

## 12. Evidence table

| # | Evidence | Reference | Class |
| --- | --- | --- | --- |
| 1 | `CREATE TABLE public.ai_content_history ( … )` | `supabase/migrations/00000000000000_init_schema.sql:1041–1060` | `DIRECT` |
| 2 | `COMMENT ON TABLE … IS 'AI generation history'` | same file, `:1060` | `DIRECT` |
| 3 | Every creation line blamed to `2d23fb89` | `git blame -L 1036,1062` | `DIRECT` |
| 4 | Introducing commit | `2d23fb892921cbc41d6c0c20b7660e86fc968178` — `CarbonTally RC2 Final database baseline`, `shomonrobie`, 2026-08-06 | `DIRECT` |
| 5 | Creation detected by `--diff-filter=A` | `git log --diff-filter=A -- supabase/migrations/00000000000000_init_schema.sql` | `DIRECT` |
| 6 | Only 4 commits ever touched that file (`eed55d6`, `2d23fb8`, `d3af816`, `dbe72aa`) | `git log --follow` | `DIRECT` |
| 7 | Banner `-- PHASE D3 CONTINUED: AI CONTENT`, added 2026-08-14 by `dbe72aa6` | `init_schema.sql:1038`; `git blame` | `DIRECT` |
| 8 | Schema-construction banners D1–D5 (foundation, core business, transactional, supporting, constraints) | `init_schema.sql:9,182,614,777,944,1038,1063,1644,2133` | `DIRECT` |
| 9 | Original design: "Purpose: Track AI-generated content with feedback"; `prompt_type` = `executive_summary`/`analysis`/`methodology`; `report_id → report_generation_queue`; two indexes | `docs/Final/UI_UX-Final_Guideline.md:495–531`; index entry `:958` | `DIRECT` |
| 10 | "AI interactions are journaled in `ai_content_history` for auditability and prompt/version traceability" | `docs/Final_Kimi/…/01_application_architecture.md:133` | `DIRECT` |
| 11 | Module purpose "Prompt/response audit" | `…/03_module_breakdown.md:277` | `DIRECT` |
| 12 | Report-audit provenance "(model, tokens, cost)" on `GET /audit/reports/{reportId}` | `…/04_api_design.md:247` | `DIRECT` |
| 13 | Rating coverage `user_rating` "CHECK 1–5" | `…/carbontally_uk_ie_review_sec03.md:112` | `DIRECT` |
| 14 | "AI usage + cost already captured — `ai_content_history` (tokens, cost, model, latency)" | `docs/ohd/reports/CT-P8X-DISCOVERY-OPERATIONAL-INTELLIGENCE-20260912-002.md:106` | `DIRECT` |
| 15 | RC2 Architecture Freeze verdict `KEEP` (all columns), section "2.13 Reports & AI content" | `docs/Final_Kimi/…/CarbonTally_RC2_Architecture_Freeze.md:284` | `DIRECT` |
| 16 | `report_generation_queue.ai_model_used/ai_tokens_used/ai_cost` described as "the committed FinOps surface" | same file, section 2.13 | `DIRECT` |
| 17 | Earlier lineage: the RC1 bundle already lists the table (2026-08-04) | `database/rc1/004_rc1_rls.sql:137` in `de94363`/`9f87229` | `DIRECT` |
| 18 | Never altered: 0 `ALTER TABLE`, 0 `ADD COLUMN` across all refs | `git log --all -S'ALTER TABLE public.ai_content_history'`, `-S'ai_content_history ADD COLUMN'` | `DIRECT` |
| 19 | RLS enabled in Phase 8; "no policy or privilege is touched" | `supabase/migrations/20260925000000_p8_rls_4b_group1_enablement.sql:56,80`; commit `1db97ba` | `DIRECT` |
| 20 | I1 does not reuse/migrate/alter/delete it; I2 does not alter it | `20261001000000_…sql:24`; `20261002000000_…sql:28` | `DIRECT` |
| 21 | Negative assertions in Insight tests | `backend/tests/unit/data/test_i1_insight_migration.py:17,134`; `test_i2_insight_authorization_contracts.py:111` | `DIRECT` |
| 22 | No ORM/class ever existed (0 hits for `AIContentHistory`/`aiContentHistory`; no `*ai_content*` file ever) | `git log --all -S…`, `git log --all --name-only -- '*ai_content*'` | `DIRECT` |
| 23 | No write statement ever existed (0 hits for `INSERT INTO …`, `UPDATE …`, `ai_content_history SET`, `delete from …`); exactly **1** read hit — a QA `SELECT count(*)` | `git log --all -S…`; `docs/verification/QA-AI-001-…:515` | `DIRECT` |
| 24 | Dormant by PO decision; options A/B/C; single bounded home; no migration now | D2 §22.2 (`:1212`), §22.3 (`:1220–1224`), §22.4 (`:1228`), R20 (`:1466`), §27.2 (`:1481`) | `DIRECT` |
| 25 | Master Spec §23 restates the dormant structure and requires the I3/I4 bounded-home decision | `CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md:1090–1100` | `DIRECT` |
| 26 | Observed 0 rows in the local demo DB; informational defect `QA-AI-001-D4` | `docs/verification/QA-AI-001-…:101,202,370,392,515,560` | `DIRECT` (observation, environment-specific) |
| 27 | Feature audit: "still dormant (0 rows, no application reference)" | `docs/audits/CT-FEATURE-AUDIT-P1-P8X-001.md:200` | `DIRECT` |
| 28 | Seed carries a header-only, data-stripped entry | `supabase/seed.sql:181` | `DIRECT` |
| 29 | Data-factory schema text mirrors the DDL; no generator code references it | `tools/carbon_data_factory/schema.txt:1041,1060` | `DIRECT` |
| 30 | Insight current-state record: Ask CarbonTally "DESIGNED / SUPERSEDED (naming only)"; dormant `ai_content_history` noted | `docs/cline/reports/CT-P8-CURRENT-STATE-RECOVERY-20260913-023.md:276` | `DIRECT` |
| 31 | Pre-baseline authorship (V1 vs V2) is absent from this repository's history | no earlier containing commit; the RC1 bundle references but does not create it | `UNKNOWN` |
| 32 | Production row presence | no repository artefact measures production | `UNKNOWN` |
---

## 13. Direct evidence vs inference vs unknown

**`DIRECT` (established by repository artefacts):**

* created only in `supabase/migrations/00000000000000_init_schema.sql:1041–1060`, introduced by `2d23fb8` (2026-08-06, "CarbonTally RC2 Final database baseline");
* original schema = 16 columns exactly as quoted in §4, unchanged to HEAD;
* documented purpose = journal AI-generated report content with prompt/model/metrics/feedback (§5);
* inherits the legacy RC1 lineage (the RC1 bundle referenced it two days before the baseline);
* never altered (0 `ALTER TABLE`, 0 `ADD COLUMN`) and never dropped;
* no application code has ever referenced it — no writer, no reader, no repository, no route, no model class, no file named `*ai_content*`;
* exactly one read reference in history: a Phase 8 QA `SELECT count(*)`;
* named by the Phase 8 RLS-enablement migration and by the I1/I2 migration comments and tests **only to disclaim touching it**;
* the dormant-table decision trail is documented (RC2 freeze `KEEP`; D2 §22 with options A/B/C and "no migration now"; R20/§27.2; Master Spec §23; QA-AI-001-D4).

**`INFERENCE`:**

* its original *producer* was pre-V3 (V1/V2-era) application code not present in this repository;
* its AI telemetry intent was in practice assumed by `report_generation_queue.ai_model_used/ai_tokens_used/ai_cost`, documented as the "committed FinOps surface";
* a non-zero production row count is unlikely given no writer exists and the local demo measurement was 0 — but unproven.

**`UNKNOWN`:**

* the exact original V1/V2 development phase or task that first authored it (pre-baseline history is absent);
* whether production (or any other environment) holds rows;
* whether any system outside this repository writes to it;
* whether an RLS policy exists beyond RLS being enabled;
* whether its rating/feedback capability (`user_rating`, `user_feedback`, `was_accepted`) is still desired — no ratified Insight document specifies it.

---

## 14. Implication for Q1

`DIRECT` — Q1 as recorded in the governing documents is: **which bounded home should hold AI interaction/cost/rating data**, with the recorded option space **Option A** (the new Insight interaction domain / Layer 2), **Option B** (an extension of the existing AI table, i.e. `ai_content_history`), **Option C** (another bounded structure) — D2 §22.3/§22.4, R20, §27.2; restated as Master Spec §23. The governing constraint is a **single** bounded home; a duplicate AI-history store is forbidden.

**What this investigation changes for Q1:**

1. `DIRECT` — "why does this table exist?" is now answered: a legacy report-generation AI-content journal inherited from the RC1/RC2 database, documented as "Track AI-generated content with feedback", with no V3/Phase-8 producer or consumer. Q1 need no longer be decided against an unexplained artefact.
2. `DIRECT` — the table is **not** an Insight artefact: I1/I2 explicitly disclaimed it, I3 has no persistence, and it carries none of the proposed Layer-2 discriminators (conversation/message link, intent, tool invocations, references, answer status, provider, correlation id) while carrying two capabilities the ratified Insight layers do not specify (rating, feedback, acceptance).
3. `INFERENCE` — Option B (extension) is therefore not a like-for-like substitute for Layer 2: it would either become a second, differently-shaped home for interaction data or require substantial extension. Option A aligns with the ratified three-layer model, and §22.4's "single bounded home" constraint would then require an explicit disposition for the legacy table (retain as-is, retire, or repurpose). Reaching either conclusion is a PO decision, not a forensic one.
4. `UNKNOWN` — the two facts that materially affect the **safety** of any option cannot be established from this repository: production row presence, and whether an external/legacy writer still exists. Also unverified: whether an RLS policy exists on the table (RLS is enabled; no policy definition was found in the inspected migrations).

**Answer to whether Q1 can now be decided from evidence:** the *facts* Q1 depended on are now established, so Q1 is **decidable on the documented record** — but the decision remains a PO policy choice, and any branch that assumes the table is empty, unreferenced in production, or safe to repurpose should first be supported by an authorised read-only production check plus confirmation that no external writer exists. This report does **not** decide Q1 and does **not** recommend an option.
---

## 15. Final forensic classification

# `PARTIALLY SUPERSEDED`

**Basis:**

* `DIRECT` — `ai_content_history` was designed as a single-purpose **report-generation AI content journal** (prompt → model → generated content → tokens/latency/cost → human rating/acceptance), scoped to an organisation and optionally to a report (§5). In that role it has **no producer in the current codebase**, and AI cost/usage telemetry for report generation is documented elsewhere as "the committed FinOps surface" (`report_generation_queue.ai_*`) — i.e. **its original functional role has been superseded**.
* `DIRECT` — yet it is **not fully obsolete or unrelated**: it carries AI **cost/rating/feedback** capability, which is exactly the subject of the still-open D2 §22 / Master Spec §23 question, and the governing documents explicitly retain it as a **candidate bounded home** (Option B) rather than discarding it — RC2 Architecture Freeze `KEEP`, and D2 §22.2 "Do NOT automatically reuse or delete it".
* `DIRECT` — it has never been altered, never dropped, never written or read by application code in this repository, and it is protected from accidental Insight coupling by explicit I1/I2 assertions.

**Alternatives considered and why not chosen:**

* `OBSOLETE PREDECESSOR` — partly supported (its original consumer is gone), but rejected as the overall classification because part of its intent (AI cost/rating/feedback storage) remains a live input to an open PO decision, and no document declares it deprecated.
* `STILL RELEVANT` — not supported: no ratified layer consumes it, and it lacks the Layer-2 discriminators.
* `UNRELATED LEGACY` — not supported: it sits in the same problem space as I4's Layer 2 (AI interaction/content history with usage/cost/rating), which is precisely why D2 §22 names it as a candidate home.
* `INSUFFICIENT EVIDENCE` — not applicable: creation, purpose, non-use and the decision trail are all established by direct evidence; what remains unresolved is a **policy disposition**, which is not a forensic classification question.

**This classification is a forensic finding only.** It is **not** a PO decision and does **not** recommend deleting, migrating, reusing, retaining or otherwise dispositioning the table. No such decision was taken, and **Q1 remains OPEN**.

**Stated limitations of this investigation:**

* no database was queried, so `PRODUCTION ROW PRESENCE NOT VERIFIED`;
* no migration, schema, application file, test, configuration or other document was modified — the only repository change is this report;
* the pre-baseline (V1/V2) authoring history is not present in this repository, so the original authoring phase remains `UNKNOWN`;
* this is Cline's own forensic analysis and has **not** been independently verified; it requires PO and/or OHD review before any decision relies upon it.
