# DEMO-T1 — Local Demo Lab (identities + infrastructure)

**Scope:** make the authoritative release reproducibly runnable on a developer machine with
**real, role-bearing synthetic identities**, so the application resolves each actor's
entity/role and enforces the correct boundaries. This provisions **identity and access
foundations only** — no factors, documents, calculations, reports, OCR policy, billing or
manual-processing governance changes.

---

## 1. Topology (local only)

```
release backend (127.0.0.1:8070)
   ├── DATABASE_URL ─────────► PostgreSQL: carbontally_demo_local  (127.0.0.1:54426)
   │                              · release schema built from supabase/migrations/*
   │                              · lab identities + relationships only
   └── SUPABASE_URL ─────────► lab gateway (127.0.0.1:54430)
                                  ├── /rest/v1 → lab PostgREST  → carbontally_demo_local
                                  └── /auth/v1 → local stack GoTrue (supabase_auth_carbon_ledger)
```

The developer's local Supabase stack (`carbon_ledger`) is **read** for schema/keys and
provides authentication; its databases — including the investor demo dataset — are never
reseeded, truncated or altered.

Containers created by this tooling (all disposable, prefixed `carbontally_demo_lab_`):

| container | role |
|---|---|
| `carbontally_demo_lab_postgrest` | REST (PostgREST) over the lab database |
| `carbontally_demo_lab_gateway` | nginx: the single localhost-published port (auth + rest) |

Ports: gateway `54430` (localhost only), lab backend `8070` (with `--backend`).

## 2. Commands

```bash
./tools/demo_lab/run_demo_lab.sh              # stack + provision + verify
./tools/demo_lab/run_demo_lab.sh --backend    # ... and start the release backend
python3 tools/demo_lab/verify.py              # re-verify (server-side)
./tools/demo_lab/reset_demo_lab.sh            # remove lab DB + containers (+ lab auth users)
./tools/demo_lab/reset_demo_lab.sh --purge-state   # also delete local credentials/evidence
```

Every step is idempotent: re-running creates nothing twice and destroys no lab data.

## 3. Actors (authoritative list: `manifest.json`)

| actor | entity | role | workspace |
|---|---|---|---|
| `platform.admin` | CarbonTally internal (platform) | staff role `admin` (`can_manage_organizations`) | `/ops` + admin control plane |
| `operator` | CarbonTally internal staff | staff role `operator` | `/ops` |
| `pe.manager` | Processing Entity Alpha | staff role `pe_manager` (entity-scoped) | `/pe` |
| `owner.a` / `admin.a` / `member.a` / `viewer.a` | Demo Lab Organisation A | owner / admin / member / viewer | `/home` |
| `owner.b` / `viewer.b` | Demo Lab Organisation B | owner / viewer | `/home` |
| `consultant.owner` / `consultant.member` | Demo Lab Carbon Consultants (firm) | owner / consultant (member capability flags all false) | `/consultant` |
| `owner.clienta` / `owner.clientb` | Client A / Client B (consultant-managed organisations) | owner | `/home` |

E-mail domain: `@demo-lab.carbontally.local` (distinct from the investor demo dataset's
`@demo.carbontally.local`).

## 4. Credentials

* **Never in the repository.** Tooling reads/writes `<state dir>` (default
  `~/ct_local_env/demo_lab/`); `credentials.local.json` is created mode `0600`.
* The lab generates its own **synthetic password** and a **JWT secret** locally; service/anon
  keys come from the *local* stack. No production credential, URL or dataset is used.
* Rotate: `./tools/demo_lab/reset_demo_lab.sh --purge-state` then `run_demo_lab.sh`.

## 5. What `verify.py` proves

* authentication per actor (password grant against the local GoTrue);
* `GET /api/v3/me/context` returns the expected **actor type, destination, organisation and
  role** for every actor;
* a probe matrix over real release gates — organisation reads, the owner/admin-only audit
  surface, the consultant plane, the PE plane, the admin control plane — each with an
  expected ALLOW or DENY;
* isolation rules: Org A ↮ Org B, Client A ↮ Client B, consultant ↮ unrelated organisation,
  customer ↮ admin plane, customer/internal staff ↮ PE plane, viewer/member ↮ owner/admin.

Evidence JSON is written to `<state dir>/evidence/` (no tokens or passwords stored).

## 6. Known limitations (recorded honestly)

1. **Authentication is delegated to the local stack GoTrue.** The lab does not run its own:
   the supabase GoTrue image migrates an existing `auth` schema but cannot bootstrap one, and
   its migrations expect objects from Supabase's platform bootstrap (e.g.
   `auth.code_challenge_method`), so a fresh isolated auth schema crash-loops. Using the
   stack's healthy GoTrue (same image) gives real password logins while adding only
   clearly-namespaced lab users to the stack's auth data.
2. **Auth vs data split.** Auth lives in the stack database, lab data in the lab database, so
   `provision.py` mirrors the 13 lab user ids into the lab database's `auth.users` to satisfy
   the release's foreign keys (ids and e-mails only — no hashes, no sessions).
3. **One release migration is tolerated, not applied:**
   `20260823000000_d32_private_documents_storage.sql` needs `storage.buckets`; the lab
   deliberately omits the storage schema (documents are a later workstream). Recorded in the
   stack summary output.
4. **F-T1-001 (product defect, outside this task):**
   `GET /api/v3/reporting/audit-activity` returns **HTTP 500** for a correctly-authorized
   organisation owner (`asyncpg: operator does not exist: uuid = text`). T1 does not fix it;
   it is reported for a separate bounded task.
5. No factors, documents, calculations, reports, MPG grants, clarification cases or
   reconciliation data are created — those belong to later demo workstreams.
