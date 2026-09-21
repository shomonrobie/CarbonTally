# CT-P8-I4-Q1-AI-CONTENT-HISTORY-DISPOSITION-PREPARATION-20260921

**Purpose:** a clean, authoritative **Q1 disposition-preparation record** for `public.ai_content_history`, incorporating the OHD-verified evidence and the corrections to the earlier Cline analyses.
**Checkout:** `/home/shomonrobie/ct_93d5cdd` · **Branch:** `p8-release-reconciled` · **Starting HEAD:** `067ce73a40ce0f01c54d799a37d89e2aa56adf0c`
**Evidence labels:** `DIRECT` = established by an inspected artefact · `INFERENCE` = reasoned from evidence · `UNKNOWN` = not established.

**Governance boundary of this task (all unchanged and untouched):** no I4 implementation; no database migration; no table rename, deletion or modification; no data migration; no RLS modification; no Prisma schema modification; no application-code modification; no Master Specification v1.2; no resolution of Q2–Q14. **Only this documentation report was created.**

**Sources reconciled:** the OHD verification `CT-P8-I4-AI-CONTENT-HISTORY-OHD-VERIFICATION-20260921.md` (the independent verification); the two Cline analyses (`…ORIGIN-FORENSIC…`, `…INSIGHT-SCHEMA-FIT…`); `CT-P8-I4-PREAUTHORIZATION-READINESS-AUDIT-20260921.md`; the D2 PO Ratification; Master Specification v1.1; plus direct inspection of `supabase/migrations/00000000000000_init_schema.sql`, `CarbonTally_DB_Schema_V3M2.sql`, `prisma/schema.prisma` and `20260925000000_p8_rls_4b_group1_enablement.sql`.

---

## 1. Corrections incorporated (from the independent OHD verification)

`DIRECT` — the following earlier Cline claims are **corrected here** rather than repeated. The two material ones come first.

| # | Severity | Earlier (incorrect) claim | Corrected, verified position |
| --- | --- | --- | --- |
| D-1 | **MATERIAL** | "the table has **zero** RLS policies … deny-by-default for `anon`/`authenticated` … cannot be read by `authenticated` at all" | **CONTRADICTED.** RLS is enabled **and four policies exist**: `CarbonTally_DB_Schema_V3M2.sql:4641` (DELETE), `:4645` (INSERT), `:4649` (SELECT), `:4653` (UPDATE), all `TO "authenticated"`; the live local Demo Lab DB confirms RLS enabled **with** those four policies. The table is therefore **more permissive** than the earlier report stated. Root cause: a **migrations-only** search using the unquoted pattern `ON public.ai_content_history`, which cannot match the dump's quoted `ON "public"."ai_content_history"`. Detail in §5. |
| D-2 | **MATERIAL** | "no ORM/model class ever existed" | **CONTRADICTED for the ORM claim**: `prisma/schema.prisma:599` declares `model ai_content_history` with **3 relations and 2 indexes**, and Prisma is a declared repository dependency. The narrower claim "no application reader/writer" remains `VERIFIED`. Detail in §4.3. |
| D-3 | Moderate | "0 `ALTER TABLE`, 0 `ADD COLUMN` across all refs" | **PARTIALLY VERIFIED** — substance holds under direct inspection, but the cited command is now self-polluted (the earlier report's own text contains those strings) and could not match the dump's quoted, line-wrapped `ALTER TABLE ONLY "public"."ai_content_history" ADD CONSTRAINT …`. |
| D-4 | Moderate | current-tree reference inventory | **PARTIALLY VERIFIED** — three omissions: `prisma/schema.prisma`; `CarbonTally_DB_Schema_V3M2.sql` (the artefact holding the policies previously reported absent); and a second DDL copy at `e2e/environment/supabase/migrations/00000000000000_init_schema.sql:1041`. |
| D-5 | Moderate | "no index"; "no FK on `report_id`"; design indexes/FK "were not shipped" | **PARTIALLY VERIFIED** — true for the migrations, the root dump and the live local DB (PK index only, organisation FK only); **not** true repository-wide, because the Prisma model declares both design indexes and the `report_generation_queue` relation. |
| D-6 | Minor | "16-column" citation attributed to `CT-P8X-DISCOVERY-…-002.md:47` | **CORRECTED** — the `ai_content_history (16)` column count is at **`:76`**; `:47` is a table header. Substance unchanged. |
| D-7 | Minor | "§15.3 requires provider **and** model **and** optional truthful `model_version`" | **PARTIALLY VERIFIED** — §15.3 requires distinguishing *configured* from *actually used* provider (never claiming AI because a provider is configured); `model_version` does not appear in the Master Specification. Truthful attribution is supported by §15.3 and §8.1 (`:436`), and the `automation_model_version` precedent is real, but the specific `model_version` requirement is not textual. |
| D-8 | Minor | "13 of 16 columns are non-report-specific" | **PARTIALLY VERIFIED** — defensible range **12–14** depending on how `prompt_type`/`content_format`/`prompt_text` are counted; interpretive aggregate, not a fact. |
| D-9 | Info | one schema declaration treated as authoritative | The repository holds **three divergent declarations** (SQL baseline; root dump; Prisma model) plus a fourth DDL copy under `e2e/`, disagreeing on varchar sizes, `numeric` vs `Decimal(10,4)`, the `was_accepted` default, FKs and indexes — an **OPEN schema-governance issue** (§4.4). |
| D-10 | Info | "the live database was not queried" | Correct and honest for the Cline reports; OHD additionally queried the **local Demo Lab** read-only, confirming 0 rows, RLS enabled and 4 policies. **Production remains unqueried.** |

`DIRECT` — OHD found **no discrepancy** in: the creation migration/lines/comment, the introducing commit and blame, the file's commit history, the original-purpose quotations, the phase-association reasoning, writer/reader absence, the "never altered (definition)" substance, the seed's data-stripped state, the AI usage/cost homes, the audit ledger's append-only trigger and taxonomy, the canonical-namespace rule, the I1/I2 disclaimers, the production-data limitation, or the scope discipline of both commits.
`DIRECT` — OHD issued **no overall PASS**: its verdict (`:394`) is "historical findings verified with corrections; schema-fit findings verified **except** the RLS-policy premise, which is contradicted".
---

## 2. Historical facts (verified)

**2.1 Creation migration** — `DIRECT`: `supabase/migrations/00000000000000_init_schema.sql`, lines **1041–1060**, under the banner `-- PHASE D3 CONTINUED: AI CONTENT` (line 1038, added later on 2026-08-14 by `dbe72aa6`), with `COMMENT ON TABLE public.ai_content_history IS 'AI generation history'`. The migration-timestamp prefix is the unordered V3 baseline `00000000000000`.

**2.2 Original purpose** — `DIRECT`: the retained design artefact (`docs/Final/UI_UX-Final_Guideline.md:495–531`) states `-- TABLE: ai_content_history` / `-- Purpose: Track AI-generated content with feedback`, with `report_id … REFERENCES report_generation_queue(id)`, `prompt_type` examples `'executive_summary'`, `'analysis'`, `'methodology'`, `content_format` examples `'text'`, `'markdown'`, `'html'`, a 1–5 `user_rating`, and the entry `ai_content_history — Track AI-generated content`. Corroborated by the retained legacy architecture set ("AI interactions are journaled in `ai_content_history` for auditability and prompt/version traceability"; module purpose "Prompt/response audit"; audit provenance "(model, tokens, cost)"), by the OHD operational-intelligence discovery ("AI usage + cost already captured — `ai_content_history` (tokens, cost, model, latency)") and by the RC2 Architecture Freeze verdict `KEEP` (all columns).

**2.3 Introducing commit** — `DIRECT`: `2d23fb892921cbc41d6c0c20b7660e86fc968178` ("CarbonTally RC2 Final database baseline"), author `shomonrobie <38324907+shomonrobie@users.noreply.github.com>`, 2026-08-06; every creation line blamed to it; the file has only four commits in its history.

**2.4 Pre-Phase-8 origin** — `DIRECT`: the RC1 database bundle (`database/rc1/004_rc1_rls.sql:137`, commits `de94363`/`9f87229`, **2026-08-04**) already enumerates the table. **No evidence associates it with product Phase 1–7**, and it is not a Phase 8 creation: it predates Phase 8 by ~5 weeks and was inherited into the V3/RC2 baseline. The only phase-like label is the schema-build section "PHASE D3 (AI CONTENT)". `UNKNOWN` — the original V1/V2 authoring phase.

**2.5 Historical application non-use** — `DIRECT` (verified): no application reader or writer has ever existed in this repository — no `INSERT`/`UPDATE`/`DELETE` statement in any commit, no service/repository/route/fixture, no file ever named `*ai_content*`, and exactly one read reference in history (a read-only QA `SELECT count(*)`). `DIRECT` (corrected per D-2): an ORM declaration **does** exist — `prisma/schema.prisma:599` `model ai_content_history`, Prisma being a declared repository dependency — but that is a *schema* declaration, not an application reader/writer; the "no application reader/writer" claim therefore stands, while the earlier "no ORM/model ever existed" claim does not.

**2.6 Current application non-use** — `DIRECT`: no runtime path reads or writes the table. Current-tree references are limited to schema declarations (migration, root dump, Prisma model, `e2e/` DDL copy), two Insight tests asserting the I1/I2 migrations do **not** touch it, the Phase 8 RLS-enablement array, the data-stripped `supabase/seed.sql` header, a data-factory schema-text copy, and documentation.

**2.7 Production-row uncertainty** — **`PRODUCTION ROW PRESENCE NOT VERIFIED`** (`DIRECT`/`UNKNOWN`): the only measurement in evidence is a read-only local **Demo Lab** observation of **0 rows** (QA-AI-001 `[OBS]`, reconfirmed by the OHD verification for that environment). No repository artefact measures production. Absence of code references must not be read as zero rows.

**2.8 External-writer uncertainty** — **`UNKNOWN`**: "no writer exists in this repository" is not "no writer exists". The table's grants include `REFERENCES, TRIGGER, TRUNCATE, MAINTAIN` for `anon`, `authenticated` and `service_role` (root dump `:5732–5734`), and `service_role` bypasses RLS on the platform's usual server-side posture, so any server-side or external path could write without leaving repository evidence.
---

## 3. Current schema facts (reconciled: SQL baseline, dump, Prisma)

**3.1 SQL baseline (primary migration source)** — `DIRECT`: 16 columns exactly as shipped: `id` (uuid PK, default `extensions.uuid_generate_v4()`), `organization_id` (uuid NOT NULL FK→`organizations(id)` ON DELETE CASCADE), `report_id` (uuid **nullable, no FK**), `prompt_type` (varchar NOT NULL), `prompt_text` (text), `model_used` (varchar), `generated_content` (text), `content_format` (varchar), `tokens_used` (integer, CHECK ≥ 0 or NULL), `processing_time_ms` (integer, CHECK ≥ 0 or NULL), `cost` (numeric, CHECK ≥ 0 or NULL), `user_rating` (integer, CHECK 1–5 or NULL), `user_feedback` (text), `was_accepted` (boolean), `created_at` (timestamptz, default `now()`, nullable), `created_by` (uuid, nullable, **no FK**). No index beyond the PK; no trigger; no column change since creation.

**3.2 Root dump** — `DIRECT`: `CarbonTally_DB_Schema_V3M2.sql` (tracked) repeats the same 16 columns, adds the named CHECK constraints (`ai_content_history_cost_check`, `…_processing_time_ms_check`, `…_tokens_used_check`, `…_user_rating_check`), records the primary key (`:3243–3244`) and the organisation FK (`:4285–4286`), and contains **no** `report_id`/`created_by` FK and **no** `idx_ai_history*` index. It is also the artefact that carries the four RLS policies (§4) — i.e. the disconfirming evidence for the earlier "zero policies" claim.

**3.3 Prisma model** — `DIRECT`: `prisma/schema.prisma:599–623` (tracked) declares `model ai_content_history` with the same 16 fields **plus** three relations and two indexes:

* `organization_members` relation on `created_by → organization_members.id` (`onDelete: NoAction`);
* `organizations` relation on `organization_id → organizations.id` (**`onDelete: NoAction`**, whereas the SQL dump specifies `ON DELETE CASCADE` — a behavioural divergence);
* `report_generation_queue` relation on `report_id → report_generation_queue.id` — the FK the SQL baseline and dump never shipped;
* `@@index([organization_id], map: "idx_ai_history_org")` and `@@index([report_id], map: "idx_ai_history_report")` — the design indexes the SQL baseline and dump never shipped;
* narrower typings than SQL: `VarChar(50)` for `prompt_type`, `VarChar(50)` for `model_used`, `VarChar(20)` for `content_format`, `Decimal(10, 4)` for `cost`, and `was_accepted Boolean? @default(true)` (no SQL default).

**3.4 Divergence — an OPEN schema-governance issue** — `DIRECT`: the repository holds **three divergent declarations** of one table (SQL baseline, root dump, Prisma model) plus a fourth DDL copy at `e2e/environment/supabase/migrations/00000000000000_init_schema.sql:1041`, disagreeing on varchar sizes, `numeric` vs `Decimal(10,4)`, the `was_accepted` default, FK presence and index presence — in addition to Prisma's `NoAction` versus SQL's `CASCADE` on `organization_id`.

Recorded consequences (to be resolved by governance, **not** resolved here):

1. **which declaration is authoritative is `UNKNOWN`/unresolved** — for migrations the SQL baseline is the correct primary source, but it is not the whole repository record;
2. the SQL migration, the root dump and the live local Demo Lab DB agree with each other (PK index only, organisation FK only, unbounded varchar/`numeric`), while the Prisma model declares an FK and two indexes that the database does not implement — so Prisma and the database **disagree**, and Prisma-generated migrations could attempt to create objects that never existed;
3. the divergence is raised as an open item by the independent verification (its §24 item 4) and must be treated as unresolved in any Q1 disposition preparation.

`DIRECT` — **no** Prisma, SQL, migration or schema change was made by this task; the divergence is recorded as found.
---

## 4. RLS facts (corrected — the earlier "zero policies" claim is withdrawn)

`DIRECT` — the verified state, superseding the earlier incorrect claim:

| Aspect | Verified position | Evidence |
| --- | --- | --- |
| RLS enabled? | **Yes** | Phase 8 enablement migration `20260925000000_p8_rls_4b_group1_enablement.sql:80` lists `'ai_content_history'` in its approved table array; the local Demo Lab DB shows `relrowsecurity = true` |
| Policies present? | **Yes — four policies**, all `TO "authenticated"` | Root dump `CarbonTally_DB_Schema_V3M2.sql:4641` (DELETE), `:4645` (INSERT), `:4649` (SELECT), `:4653` (UPDATE); the local Demo Lab `pg_policies` returns exactly those four rows (`ai_content_history_tenant_select/insert/update/delete`, `{authenticated}`) |
| SELECT scope | **Organisation- or consultant-scoped**: `public.is_org_member(organization_id) OR public.is_org_consultant(organization_id)` | dump `:4649` |
| INSERT scope | **Organisation-member scoped**: `is_org_member(organization_id)` (WITH CHECK) | dump `:4645` |
| UPDATE scope | **Organisation-member scoped**: `is_org_member(organization_id)` (USING + WITH CHECK) | dump `:4653` |
| DELETE scope | **Organisation-member scoped**: `is_org_member(organization_id)` (USING) | dump `:4641` |
| Creator-private predicate? | **Absent** — no `auth.uid()` term in any of the four policies | dump `:4641–4653` |
| Mutability | **Mutable by organisation members** (UPDATE and DELETE policies exist) | dump `:4653`, `:4641` |
| `service_role` | Bypasses RLS (platform posture) and holds the table's grants | dump `:5734`; platform convention |
| Corroborating in-repo guard | The very migration cited for enablement contains `IF pol_count = 0 THEN RAISE EXCEPTION 'RLS-4B guard: public.% has no policy; refusing to enable RLS (deny-all risk)…'` applied to an array that **includes this table** — it could not have completed had the table no policy | enablement migration body |

**Consequences that follow from the corrected position:**

1. `anon`/`authenticated` are **not** deny-by-default here. Any organisation member — and, for SELECT, a consultant with an active client grant per `is_org_consultant` — can read rows, and organisation members can also insert, update and delete them through the authenticated/PostgREST path.
2. The policy set is therefore **not I2 creator-private Insight authorization**. I1/I2's model is organisation membership **and** creator-private visibility (`is_org_member(organization_id) AND created_by = auth.uid()`), with authenticated limited to SELECT+INSERT and UPDATE/DELETE revoked; this table grants broader, mutable access with **no creator predicate**.
3. It is also **not an audit-grade structure**: `public.audit_trail` is append-only under the Phase 7 trigger, whereas this table is directly mutable by organisation members.
4. Any future reuse of this table (or of a successor that inherits its posture) would require **policy reconciliation/replacement** — tightening to the I2 creator-private contract plus a mutability decision — and not first-time policy creation. The derived architectural statement "reuse requires policy work" survives, but its premise and character are corrected: the work is to **replace/tighten an existing permissive, non-creator-private, mutable policy set**, together with the granted INSERT/UPDATE/DELETE.
5. **Live production RLS state is `UNKNOWN`** — the confirmation above covers the repository dump and the local Demo Lab only; production was not queried.

`DIRECT` — **no RLS policy, grant or privilege was modified by this task.** The four policies, the grants and the enablement state are recorded exactly as found.
---

## 5. Domain separation (these must not be collapsed)

`DIRECT` — four distinct domains are involved, and merely because `ai_content_history` contains AI-related fields it does **not** follow that one structure may serve any two of them. Master Spec §20.1 states the layers "must not be collapsed":

```text
Layer 1 — Conversation / messages
  public.carbontally_insight_conversations / _messages (built at I1)
  conversation identity, message stream, author kind, ordinal ordering,
  creator-private RLS, anon denial, authenticated SELECT+INSERT only

Layer 2 — Insight interaction
  the proposed I4 record: who asked → interpreted request → authorized tool
  invocations → authoritative references → provider/model used → answer status
  → answer produced  (Master Spec §8.1, §9.3)  [does not exist yet]

AI generation
  the individual model call: prompt/reference context, generated content,
  format, provider/model (when truthfully known), latency, tokens, cost,
  finish reason, feedback/acceptance, evaluation

Canonical audit
  public.audit_trail — append-only (Phase 7 trigger), taxonomy with no AI
  category, payloads excluded (§20.4); an AI audit event would reference the
  durable interaction record rather than carry its content
```

`DIRECT` — what belongs where, stated for Q1 clarity:

| Concept | Correct home |
| --- | --- |
| conversation + messages + raw user question + creation order | **Layer 1** (built, I1, canonical namespace) |
| interaction identity, intent, tool invocations, references, answer status, correlation ids | **Layer 2** (to be authorised) |
| individual AI generation: content, provider/model, latency, tokens, cost, finish reason | **AI generation** record — the only role `ai_content_history`'s shape could plausibly serve |
| feedback, rating, acceptance | **AI generation / evaluation** — no ratified Insight layer specifies these |
| "the interaction occurred" event, immutability, investigation trail | **Canonical audit** (`audit_trail`) |

`INFERENCE` — `ai_content_history` currently **mixes** content, telemetry and human feedback in a single table; that is the same kind of collapse §20.1 prohibits, and it is one reason a reused table would need an explicit boundary even if the PO chose to restructure it. `DIRECT` — it also lacks every Insight discriminator (conversation, message, interaction, intent, tool call, reference, status, correlation), so nothing in the current Insight architecture consumes it, and nothing in it can stand in for Layer 1, Layer 2 or the ledger.

---

## 6. The Q1 architectural boundary

**6.1 NOT appropriate — directly using the existing table AS-IS as any of the following** (`DIRECT`): each statement below rests on verified gaps, not on preference.

| Proposed AS-IS role | Verdict | Evidence-based reason |
| --- | --- | --- |
| **I4 conversation storage** | **NOT appropriate** | Layer 1 is already built, ratified and canonically named (`carbontally_insight_conversations`), with `UNIQUE (conversation_id, ordinal)` ordering and creator-private RLS; this table has neither conversation identity nor `ordinal` nor a creator predicate |
| **I4 interaction storage** | **NOT appropriate** | Missing interaction identity, intent, tool invocations, references, answer status, correlation id, provider/model-version, lifecycle status — i.e. everything §9.3 requires for reconstructability |
| **canonical Insight audit ledger** | **NOT appropriate** | The ledger is `public.audit_trail`, append-only by trigger, with §20.4 excluding payloads; this table is directly mutable by organisation members and content-bearing, and it is not append-only |
| **canonical Layer-1 message store** | **NOT appropriate** | Duplicates an existing ratified store outside the canonical `carbontally_insight_*` namespace, and cannot satisfy I2's creator-private contract or I1's ordering/creation invariants |

**6.2 Potentially useful in the future — architectural potential only** (`DIRECT` capability, `INFERENCE` as potential): the columns that are **not** report-specific, and that no other ratified structure provides in a per-generation form, are:

* generated content (and its format);
* model attribution (`model_used`, noting the corrected §15.3 position that provider/model attribution must be truthful when known, and that the Gate-5 precedent adds provider and version);
* token usage;
* latency;
* cost;
* user rating;
* feedback;
* acceptance.

`DIRECT` — **this is architectural potential, NOT authorization to implement.** It does not approve reuse, extension, migration, renaming or retirement, and it does not resolve Q1. Any exploitation of that potential would additionally require: policy replacement to I2-consistent creator-private posture; a decided parent linkage; an index design; a naming/namespace decision (D2 R24); a resolved Prisma-vs-SQL authority question; and the I7 privacy position on raw prompt storage.
---

## 7. The three architectural possibilities (documented, not ranked, not selected)

`DIRECT` — these are the D2 §22.3 options, restated with the OHD-corrected evidence. **No option is ranked, recommended or selected here**, and each carries unresolved prerequisites (§8).

### Option A — Evolve/restructure the legacy table into the bounded home

D2 §22.3 describes this as "an **extension** of the existing AI table". `DIRECT` — what the verified evidence shows the work would involve, recorded as scope (not as a plan): additive generation/telemetry columns (provider, model version, finish reason, correlation identifier); a decided parent linkage (conversation/interaction), which the table has never had; resolution of the `NOT NULL` report-section `prompt_type` semantics for Insight rows; creator-presence semantics (`created_by` is nullable and carries no predicate); **replacement/tightening of the four existing permissive, mutable, non-creator-private policies** to the I2 creator-private contract, plus a mutability decision; index design (the table has only the PK index in SQL); a naming/ownership decision, because D2 R24 reserves `carbontally_insight_*` for new implementation while this table keeps a D3-era legacy name; reconciliation of the Prisma-vs-SQL declaration divergence; and — before any of it — a data review, because production row presence is unverified.

### Option B — Create/evolve a canonical Insight AI-generation structure while preserving the legacy table

`DIRECT` — a structure created under the ratified namespace (`carbontally_insight_*`) would remove the naming conflict, allow correct parentage and I2-consistent creator-private policies from the outset, permit indexes matched to real query patterns, and avoid touching legacy data or legacy semantics. `DIRECT` — its cost is that it introduces a second AI-content table, which D2 §22.4 / Master Spec §23 permit only if it is declared the single bounded home and the legacy table's disposition is decided at the same time; it also requires an authorised migration, real repository wiring proven through the real `RepositoryBundle` factory path (the I3 D-01 lesson), and explicit boundaries so per-generation telemetry does not duplicate `report_generation_queue.ai_*` (the committed FinOps surface) or `usage_tracking` aggregates.

### Option C — Retain the legacy table unchanged and defer any future disposition

`DIRECT` — this is the current, compliant holding position: D2 §22.2 states "Do NOT automatically reuse or delete it. **No migration is authorised now.**" It changes nothing, exposes no legacy data, preserves both Option A and Option B for later, and respects AGENTS.md §66/§79 (reuse existing schema where it already supports a requirement; do not remove legacy structures without an authorised disposition). `DIRECT` — its cost is that Q1 remains open, so any I4 implementation requiring a persisted generation record cannot proceed; the legacy anomalies (Prisma/SQL divergence, permissive mutable policy set, unknown production data) remain on the record; and the single-bounded-home constraint still has to be satisfied whenever any new structure appears.

`INFERENCE` — the three options differ in *where* the bounded home sits and *what has to be reconciled first*; they do not differ in the prerequisite evidence, which is the same for all three (§8).

---

## 8. Unresolved evidence (preserved, not inferred)

`DIRECT`/`UNKNOWN` — all of the following remain unresolved and none is inferred here:

1. **Production row presence** — `PRODUCTION ROW PRESENCE NOT VERIFIED`.
2. **External/legacy writer** — `UNKNOWN`; no repository writer exists, which is not the same as no writer.
3. **Original V1/V2 authoring** — `UNKNOWN`; pre-baseline history is absent from this repository.
4. **Live production RLS state** — **not verified**; the confirmed four-policy state covers the repository dump and the local Demo Lab only.
5. **Live production Prisma/schema correspondence** — **not verified**; whether production matches the SQL baseline, the dump, or the Prisma declaration is unknown.
6. **Prisma-vs-SQL schema authority** — **unresolved**; the three (four, with the `e2e/` copy) declarations disagree, and the Prisma model declares an FK and two indexes the database does not implement (raised by the independent verification, its §24 item 4).
7. **I7 privacy decision** — unresolved: retention, deletion, export, residency, provider retention, and the raw-prompt-storage-versus-hash question (§41 PR-EX3) are all open, and they determine where prompt text may live at all.
8. **Q2–Q14** — unresolved: canonical AI audit ledger (Q2), answer-status enumeration (Q3), raw question storage (Q4), Layer-2 mutability (Q5), Layer-1 lifecycle status (Q7), plus the deferred I7/I8 items.

`DIRECT` — additional evidence required before **any** future migration/repurposing (same list for every option): an authorised read-only production count and distribution; an external-writer assessment (grants/policy inventory plus provider-level access review, noting `service_role` bypasses RLS); a live policy/privilege/constraint inventory per environment; a product statement on whether AI-generated report narrative is ever returning; the I7 privacy position; an explicit naming/ownership decision if reuse is chosen; and a decision on which of the divergent schema declarations is authoritative.
---

## 9. Evidence table

| # | Evidence | Reference | Class |
| --- | --- | --- | --- |
| 1 | Creation: 16-column `CREATE TABLE public.ai_content_history` + comment `'AI generation history'` | `supabase/migrations/00000000000000_init_schema.sql:1041–1060` | `DIRECT` |
| 2 | Introducing commit / author / date | `2d23fb892921cbc41d6c0c20b7660e86fc968178`, `shomonrobie`, 2026-08-06 (`git blame -L 1036,1062`) | `DIRECT` |
| 3 | Banner `-- PHASE D3 CONTINUED: AI CONTENT` added later | `init_schema.sql:1038`; `git blame` → `dbe72aa6` (2026-08-14) | `DIRECT` |
| 4 | Original purpose | `docs/Final/UI_UX-Final_Guideline.md:495–531` ("Track AI-generated content with feedback") | `DIRECT` |
| 5 | Pre-Phase-8 lineage | `database/rc1/004_rc1_rls.sql:137` in `de94363`/`9f87229` (2026-08-04) | `DIRECT` |
| 6 | Root dump: DDL, constraints, PK, organisation FK | `CarbonTally_DB_Schema_V3M2.sql:313–340`, `:3243–3244`, `:4285–4286` | `DIRECT` |
| 7 | **Four RLS policies** (DELETE/INSERT/SELECT/UPDATE, `authenticated`, org/consultant scoped, no creator predicate) | `CarbonTally_DB_Schema_V3M2.sql:4641`, `:4645`, `:4649`, `:4653` | `DIRECT` |
| 8 | Table grants `REFERENCES, TRIGGER, TRUNCATE, MAINTAIN` to anon/authenticated/service_role | `CarbonTally_DB_Schema_V3M2.sql:5732–5734` | `DIRECT` |
| 9 | Phase 8 RLS enablement naming the table (+ no-policy guard) | `20260925000000_p8_rls_4b_group1_enablement.sql:80` and its guard body | `DIRECT` |
| 10 | Live local Demo Lab: RLS enabled, 4 policies, 0 rows | OHD verification `CT-P8-I4-AI-CONTENT-HISTORY-OHD-VERIFICATION-20260921.md:230`, `:374` | `DIRECT` (local environment only) |
| 11 | **Prisma model with 3 relations + 2 indexes** | `prisma/schema.prisma:599–623` (reverse relations at `:2083`, `:2236`, `:2667`) | `DIRECT` |
| 12 | Prisma/SQL divergence (varchars, `Decimal(10,4)`, `was_accepted` default, FKs, indexes, `NoAction` vs `CASCADE`) | `prisma/schema.prisma:599–623` vs `CarbonTally_DB_Schema_V3M2.sql:313–334`, `:4285–4286` | `DIRECT` |
| 13 | Fourth DDL copy | `e2e/environment/supabase/migrations/00000000000000_init_schema.sql:1041` | `DIRECT` (per OHD D-4) |
| 14 | No application reader/writer; one read reference (QA `SELECT count(*)`) | `git log --all -S…`; `docs/verification/QA-AI-001-…:515` | `DIRECT` |
| 15 | I1/I2 disclaimers and negative tests | `20261001000000_…sql:24`; `20261002000000_…sql:28`; `tests/unit/data/test_i1_insight_migration.py:17,134`; `test_i2_insight_authorization_contracts.py:111` | `DIRECT` |
| 16 | Dormant-by-decision, options A/B/C, single bounded home | D2 §22.2 (`:1212`), §22.3 (`:1220–1224`), §22.4 (`:1228`), R20 (`:1466`), §27.2 (`:1481`) | `DIRECT` |
| 17 | Dormant AI structure + bounded-home requirement | Master Spec v1.1 §23 (`:1090–1100`) | `DIRECT` |
| 18 | Canonical namespace for new implementation | D2 R24 / §3.2 / §3.8 | `DIRECT` |
| 19 | Canonical ledger append-only trigger; taxonomy without AI category | `20260912000000_p7_audit_immutability_and_indexes.sql:32–49`; `backend/domain/audit.py` | `DIRECT` |
| 20 | OHD corrections D-1…D-10 (RLS, ORM, search-method, inventory, indexes/FK, citations, interpretation) | `CT-P8-I4-AI-CONTENT-HISTORY-OHD-VERIFICATION-20260921.md` §21, §23, §24 | `DIRECT` |
| 21 | Production row presence; external writers; V1/V2 authorship; live production RLS/Prisma correspondence; schema authority | no repository artefact establishes them | `UNKNOWN` |

---

## 10. Verification and limitations

`DIRECT` — this task's own verification: starting HEAD `067ce73a40ce0f01c54d799a37d89e2aa56adf0c`; branch `p8-release-reconciled`; remote `github/p8-release-reconciled` aligned (`0 0`) before and after; working tree clean before the write and after the commit; the only repository change is this report; `git diff --name-only` empty (no modified tracked files).

`DIRECT` — **limitations:** no database was queried by this task (the live-Demo-Lab facts are cited from the OHD verification, not re-measured); production RLS/privilege and row state remain `UNKNOWN`; the Prisma-vs-SQL authority question is recorded, not resolved; the original V1/V2 authoring history is absent from this repository; and this record relies on the OHD verification for the corrected truth of the two material claims. It has not itself been independently verified.

---

## 11. Q1 PO DECISION INPUT — NOT A DECISION

> The existing `public.ai_content_history` table should not be directly reused AS-IS as the I4 interaction or conversation store. Its historical AI-generation fields may have future value for broader CarbonTally Insight AI-generation/evaluation capabilities, but no reuse, migration, modification, rename, deletion, or replacement is authorized by this task. Its future disposition remains a PO decision.

`DIRECT` — Q1 is **not closed** by this record. **No option (A, B or C) has been selected, ranked or recommended.** Q2–Q14 remain unresolved. I4 remains **NOT AUTHORIZED**. The table, its four RLS policies, its grants, the migrations, the Prisma schema and all application code are **unchanged** by this task.
