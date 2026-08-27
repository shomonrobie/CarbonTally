# CarbonTally V3 — Git History Secret Remediation — Expanded Scope Execution Report

**Status: EXPANDED REWRITE COMPLETE & FULLY VERIFIED IN ISOLATED MIRROR — NO PUSH (HARD STOP before any force push).**
**Date:** 2026-08-25

---

## 1. Product Owner Decision Summary

The Product Owner authorized expanding the remediation scope to include two newly discovered credential-bearing artifacts:

1. **`create_admin_dashboard.py`** — INCLUDE (investigate first; obsolete/unused → removal; useful → scrub).
2. **`frontend/.env`** — INCLUDE the historical credential-bearing version (the `8b59378` version containing `SUPABASE_SERVICE_KEY` + `RESEND_API_KEY`) in the rewrite.

All previously approved paths remain in scope. Scope must NOT expand to arbitrary files merely containing credential-like strings. No credential values are reproduced anywhere.

## 2. create_admin_dashboard.py — Investigation Findings

| Question | Finding |
|---|---|
| Purpose | One-off **project-structure generator** for the admin dashboard ("CarbonTally Admin Dashboard - Project Structure Generator", 546 lines); writes folder skeletons and a `.env` template to disk |
| Currently used? | **No.** 0 imports/references in any source; only referenced in the documentation module inventory (`docs/cline/CarbonTally_Backend_Module_Inventory_V3.md`), which classifies it as **"NO DIRECT V3 IMPACT"** with 0 reference counts |
| Required? | **No.** No build/deploy/route references it; the `admin/` app it scaffolds already exists as a built application |
| Hard-coded credential in current tree? | **Yes** — line 163 `REACT_APP_SUPABASE_SERVICE_KEY=<value>` (value REDACTED); also an anon-key line 162 |
| Could the credential be replaced with an env variable? | Technically yes (it is a Python-generated `.env` template), but the file is obsolete/unused |
| Git history | Added in `a16ba01` (same commit that removed the `.env` files); unchanged since |

**Conclusion: obsolete and demonstrably unused** → per the PO's sanctioned branch, **removed from the remediation** (path removed from all history). The original file remains recoverable from the preserved rollback bundle.

## 3. Approved Expanded Remediation Manifest

| PATH | CREDENTIAL TYPE | HISTORICAL RANGE | CURRENT-TREE STATUS | ACTION |
|---|---|---|---|---|
| `tools/carbon_data_factory/deeepseek_api.txt` | LLM provider API key (`sk-…`) | `2d23fb8` → `a909cbe` | absent (removed `878bd0f`) | REMOVE FROM HISTORY |
| `.env` | SUPABASE_SERVICE_KEY, RESEND_API_KEY | `8b59378` → `a16ba01` | absent (removed `a16ba01`) | REMOVE FROM HISTORY |
| `backend - backup.zip` | inner `backend - backup/.env` (SERVICE_KEY, RESEND_API_KEY) + `.env.test` | `2d23fb8` → HEAD | **tracked at HEAD** | REMOVE FROM HISTORY + TREE |
| `frontend/.env` | SUPABASE_SERVICE_KEY, RESEND_API_KEY (8b59378 version) | `7ca9533` → `a16ba01` | absent (removed `a16ba01`) | REMOVE FROM HISTORY |
| `create_admin_dashboard.py` | hard-coded `REACT_APP_SUPABASE_SERVICE_KEY` (line 163) | `a16ba01` → HEAD | **tracked at HEAD** | REMOVE FROM HISTORY + TREE (obsolete/unused) |

**Explicitly EXCLUDED** (per PO instruction #4): `docs/sample_bills/scope1_industrial_thermal_energy.pdf` and `docs/sample_bills/uk_waste_transfer_note.pdf` — matched a generic `sk-…` pattern inside binary PDF content but are **probable false positives** (unchanged legitimate sample documents, not confirmed credential-bearing). No other files were expanded into scope.

## 4. Pre-Rewrite Baseline (unchanged)

- Live repo HEAD / origin/main: `9458067c073bdaedae2a621b9cee42e419f14a75`; 71 commits; 0 staged; working tree residue (546 modified / 151 deleted / 57 untracked) untouched.
- Live remote: **not modified** (no push).
- Preserved rollback bundle: `/tmp/carbontally_pre_rewrite.bundle` (verified, **not overwritten**).
- Prior 3-path mirror retained at `/tmp/carbontally_rewrite.git` (HEAD `0812b015…`) — superseded but intact.

## 5. Rewrite Environment & Method

- New isolated mirror: `git clone --mirror https://github.com/shomonrobie/CarbonTally.git /tmp/carbontally_rewrite_expanded.git` (contains only `refs/heads/main` + 3 tags).
- Tool: `/tmp/git-filter-repo` (standalone official script, version `31ebad4c8fb3`).
- Command (exact-path; `--invert-paths`):
  ```
  /tmp/git-filter-repo --path tools/carbon_data_factory/deeepseek_api.txt --path .env \
      --path 'backend - backup.zip' --path frontend/.env --path create_admin_dashboard.py \
      --invert-paths --force
  ```
- Parsed 71 commits; new history written; old objects repacked/cleaned; origin remote auto-removed (expected).

## 6. New Canonical SHAs (expanded mirror — NOT pushed)

| Ref | OLD | NEW |
|---|---|---|
| `main` / D20–D37 release | `9458067c073bdaedae2a621b9cee42e419f14a75` | **`d4dcca1eb11f86bcae497815c8592d688a7e305f`** |
| `rc2-final` | `2d23fb892921cbc41d6c0c20b7660e86fc968178` | `eed55d62ee9f103279d0d2a94006952a517d3bde` |
| `v2.1-phase4` | `be405d85b53e6145bc8deff7195d2542eb3cb902` | `16d5519de621bc9c28b5a9e65efa851be8b07d5f` |
| `v2.1.1-phase3` | `ae1d68557e55704b1f99eea097f62555fd47dc4a` | `0c55c8be5bace961eb00a8158f776812e0ce74b8` |

Commit count: **70** (the empty `878bd0f` "Remove exposed API key file" commit was dropped, as in the prior rewrite). Release subject unchanged: `feat(v3): commit D20-D37 commercial platform release`.

---

## 7. Verification Results

| # | Check | Result |
|---|---|---|
| 1 | Five approved paths absent from rewritten current tree | ✅ ABSENT (all 5) |
| 2 | Five approved paths absent from reachable rewritten history | ✅ 0 objects each |
| 3 | `frontend/.env` historical credential version removed | ✅ 0 objects |
| 4 | `create_admin_dashboard.py` removed | ✅ 0 objects |
| 5 | D20–D37 release content present (13 spot-checked files: billing api/service/data/domain, main, router, App.js, BillingPage, CommercialTab, D37 migration, tests, reports) | ✅ all OK |
| 6 | Tree equivalence vs `9458067` (byte-sorted) | ✅ **exactly 2 removals**: `backend - backup.zip`, `create_admin_dashboard.py` — all 1,507 other files identical |
| 7 | Branch topology | ✅ single linear `main` |
| 8 | Tags valid | ✅ 3 tags point to rewritten commits |
| 9 | Repository integrity | ✅ `git fsck --full` clean |
| 10 | No secret values printed | ✅ (values never reproduced) |
| 11 | Approved-manifest credential strings in reachable objects | ✅ **0** matches for `SUPABASE_SERVICE_KEY=`/`RESEND_API_KEY=` value patterns |
| 12 | Remaining pattern matches | only 2 binary PDF false positives (`docs/sample_bills/*.pdf`) — excluded per PO instruction #4 |
| 13 | New HEAD tree file count | 1,507 (old 1,509 − 2 removed) |

## 8. D20–D37 Preservation (PO instruction #7)

Confirmed: all legitimate release content remains — backend billing slice (`v3_billing.py`, `v3_commercial.py`, `services/data/domain/billing.py`), composition root (`main.py`, `router.py`), frontend (`App.js`, V3 pages incl. `BillingPage.jsx`, `CommercialTab.jsx`), all D20–D37 migrations, tests, and documentation. The two removed paths (`backend - backup.zip`, `create_admin_dashboard.py`) are not part of the D20–D37 release manifest.

## 9. Removed Historical Paths — Final Confirmation (PO instruction #8)

| Path | Objects remaining in rewritten history |
|---|---|
| `tools/carbon_data_factory/deeepseek_api.txt` | 0 |
| `.env` | 0 |
| `backend - backup.zip` | 0 |
| `frontend/.env` | 0 |
| `create_admin_dashboard.py` | 0 |

The rewritten history contains **no confirmed credential-bearing artifacts from the approved expanded manifest**.

## 10. Rollback & Backup Status (PO instruction #9)

- `/tmp/carbontally_pre_rewrite.bundle` — **preserved, not overwritten** (verified "The bundle records a complete history").
- `/tmp/carbontally_rewrite.git` (prior 3-path mirror, `0812b015…`) — retained.
- `/tmp/carbontally_rewrite_expanded.git` — the verified expanded mirror (`d4dcca1e…`), **NOT pushed**.
- PO external full-folder backup — untouched.

## 11. What Was NOT Done (PO instructions #10–#15)

- ❌ NO push / force-push to the live remote (remote remains at `9458067…`).
- ❌ NO modification of the live remote.
- ❌ NO application/database/RLS/billing changes.
- ❌ NO unrelated repository cleanup.
- ❌ NO developer working-repository alignment.
- ❌ NO prune/gc of the live repo (local `refs/cline/checkpoints/*` remain untouched for now).

## 12. HARD STOP

- New rewritten HEAD (mirror only): **`d4dcca1eb11f86bcae497815c8592d688a7e305f`** — 70 commits, verified, fsck clean.
- Live repo/remote unchanged at `9458067c073bdaedae2a621b9cee42e419f14a75`.
- **STOP — awaiting the Product Owner's next decision on whether the verified expanded mirror is authorized for remote replacement.** If authorized, the execution sequence is: re-add origin on the mirror → `git fetch origin` (lease baseline) → `git push --force-with-lease origin main` → push the three rewritten tags → remote verification → non-destructive dev-repo alignment → local checkpoint-ref prune + `gc --prune=now` → final verification.

---

*End of report. SECRET VALUE NOT REPRODUCED.*
