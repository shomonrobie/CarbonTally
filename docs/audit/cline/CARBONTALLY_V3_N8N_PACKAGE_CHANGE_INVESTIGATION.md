# CarbonTally V3 — n8n-nodes-pollinations Package Change Investigation

**Task type:** READ-ONLY INVESTIGATION.
**Executed:** Read-only git diff/status/log inspection, source and documentation search, and lockfile analysis. **No staging, unstaging, commit, push, reset, restore, delete, or package installation was performed. No file was modified except this report.**
**Date:** 2026-08-25

---

## 1. What changed in root `package.json` vs HEAD

**Exactly one line added** (dependencies block):

```
+    "n8n-nodes-pollinations": "^1.0.6",
```

No other change: name, version, scripts, devDependencies, and all other dependencies are byte-identical to HEAD (`git diff package.json` shows only this single `+` line).

---

## 2. What changed in root `package-lock.json` vs HEAD

**Pure insertion of 664 lines** (56 new `node_modules/` entries) — `git diff --stat package-lock.json` reports `1 file changed, 664 insertions(+)`, and the only `-` line in the diff is the `--- a/package-lock.json` header.

The added subtree is the full dependency tree of `n8n-nodes-pollinations`:

`@n8n_io/riot-tmpl`, `@n8n/errors`, `@n8n/expression-runtime`, `@n8n/tournament`, `assert`, `ast-types`, `available-typed-arrays`, `call-bind`, `call-bound`, `callsites`, `define-data-property`, `define-properties`, `eslint-config-riot`, `esprima`, `esprima-next`, `for-each`, `generator-function`, `has-property-descriptors`, `inherits`, `is-arguments`, `is-callable`, `is-generator-function`, `is-nan`, `is-regex`, `is-typed-array`, `isolated-vm`, `jmespath`, `jsonrepair`, `jssha`, `luxon`, `n8n-nodes-pollinations`, `n8n-workflow`, `node-gyp-build` (+ nested `node_modules/*` entries for `js-base64`, `lodash`, `form-data`, `uuid`, `zod`, etc.).

**No existing lock entry was modified or removed** — no version bumps, no integrity changes to packages already in the lockfile.

---

## 3. Is the only meaningful change the addition of n8n-nodes-pollinations?

**Yes.** `package.json`: one dependency line. `package-lock.json`: the corresponding dependency subtree, additions only. There is no other meaningful change in either file.

---

## 4. Did any other dependency/configuration/scripts change?

**No.** `package.json` scripts, devDependencies, repository metadata, and all other fields are unchanged. The lockfile contains no deletions or modifications of existing entries. `frontend/package.json` and `admin/package.json` are untouched (their lockfiles show only unrelated pre-existing integrity hashes that happen to match a grep for the string "n8n").
---

## 5. When/how does this change appear in local Git evidence?

- **File mtime:** both files show `Aug 25 17:12` — i.e., they were written during the D20–D37 staging session (the staging task's final verification had already recorded this external modification).
- **Git history:** `git log --all --oneline --grep='n8n|pollinations' -i` returns **nothing**; `git log --oneline -- package.json` shows only the pre-existing commits (`8b59378`, `48be275`, `2d23fb8`). The change exists **only in the working tree** (unstaged) and has never been committed.
- **Install evidence:** `node_modules/n8n-nodes-pollinations/` is present (LICENSE, README.md, dist) — an actual `npm install` of the package was executed at the repository root, which wrote both files.
- **Originating process:** not identifiable from repository evidence (no reflog entry for working-tree file writes; only mtime and content are determinable). Environmental observation: the terminal during the staging session repeatedly echoed unrelated n8n-workflow prompt text (OpenRouter `sk-or-v1-…` placeholder, `HTTP-Referer: https://n8n.io`, `X-Title`, Pollinations.ai image API), consistent with a **parallel n8n automation experiment running on this machine outside the CarbonTally repo**. This observation is consistent with the change but does not establish who invoked it or why. Per the investigation rules, intent is **not inferred**.

---

## 6. Does any CarbonTally source import or reference n8n-nodes-pollinations?

**No.** Searches for `n8n`/`pollinations` across `frontend/src`, `backend/**`, `tools/`, and `scripts/` (excluding `node_modules`/`.git`) return **zero** references. The staged release (220 files) contains no file that imports, requires, or mentions the package.

---

## 7. Is it related to D20–D37?

**No.** The D20–D37 release manifest (preparation report Appendix C) does not include root `package.json`/`package-lock.json`; the frontend build uses `frontend/package.json` (separate, untouched); no D-series module references n8n. The staged set contains neither package file (verified: staged count for `^package(\.lock)?\.json$` = 0).

---

## 8. Is it related to the CarbonTally blog CMS?

**No.** `docs/architecture/CARBONTALLY_BLOG_CMS_DECISIONS.md` defines a **Supabase-based** blog CMS (Supabase Auth, PostgreSQL, Storage buckets) and contains **no n8n or pollinations reference** (verified by grep).

---

## 9. Is it related to any current n8n integration or automation work?

**No evidence of current n8n integration in this repository.** There are no n8n workflow files, exports, configuration, or runtime code anywhere in the repo (`find` for `*n8n*`/`*workflow*.json` outside `node_modules` returned nothing). The only n8n mentions are:
- `docs/architecture/TechnologyStack.md` — an **aspirational/recommendation** document: "Workflow Automation — n8n ⭐⭐⭐⭐⭐ / You already use n8n…" and an architecture diagram (Next.js + Supabase + AI Services + n8n). This document also recommends **Next.js**, which CarbonTally does **not** use (the frontend is Create-React-App), so the document describes a proposed target architecture, not the actual current stack. It is a tracked historical/reference document.
- `docs/CarbonTally Complete Customer Feature List.md` line 558 — a single historical bullet "‑ n8n" in a generic integrations list (next to Slack, Zapier), no detail.

Neither document ties n8n to any implemented feature or to the blog CMS.
---

## 10. Would removing/reverting the change affect the staged D20–D37 release?

**No.** The staged 220-file set:
- does **not** contain root `package.json` or `package-lock.json` (verified: 0 in `git diff --cached`), and
- contains **no** file that references n8n or pollinations.

Reverting the two working-tree files to HEAD (a future PO-authorized action — **not performed here**) would change nothing in the staged release. The root package.json is the "carbon-ledger-monorepo" wrapper whose dependencies (`prisma`, `@snaplet/seed`, `@faker-js/faker`) belong to the previously identified abandoned Snaplet/Prisma experiment; it is not part of the release build path for `frontend/` (which uses its own `package.json`).

---

## 11. Are the package files currently staged or unstaged?

**Unstaged.** `git diff --cached --name-only | grep -cE '^package(\.lock)?\.json$'` = **0**. Both remain unstaged working-tree modifications (as during the staging task).

---

## 12. Do the preparation/staging reports provide evidence explaining the change?

- The **staging report** (`CARBONTALLY_V3_D20_D37_RELEASE_STAGING_REPORT.md`, §1/§5/§23/§24/Appendix B) records the change as an **external-environment modification detected during the task** (mtime 17:12, added `n8n-nodes-pollinations`), confirms it was **not staged**, and flags it for PO review with a recommendation to revert. It does not attribute an author or reason.
- The **preparation report** (`CARBONTALLY_V3_D20_D37_GIT_RELEASE_PREPARATION_REPORT.md`) predates the change and does not mention it.
- Neither report explains who or why — consistent with the investigation's finding that the origin is an external process.

---

## Classification

### B. UNRELATED — SHOULD REMAIN UNSTAGED

Evidence basis:
- Determinably unrelated to the D20–D37 release (no source references, not in the release manifest, not in the staged set, absent from git history).
- Not related to the blog CMS (Supabase-based per the blog CMS decisions document).
- Not evidence of a current CarbonTally n8n integration (no workflows, no runtime, no imports; the TechnologyStack recommendation is aspirational and superseded — it also proposes Next.js).
- The change is a root-level `npm install` of an n8n community node (`n8n-nodes-pollinations` → Pollinations.ai) executed by an external process on this machine; who/why is not determinable from repository evidence.

**Recommendation:** leave `package.json` and `package-lock.json` **outside the D20–D37 commit** (they already are unstaged). The Product Owner should decide whether to revert the working-tree change before the commit task (recommended, to keep the root package files at HEAD) — and, separately, whether any n8n automation work is intended (no repo evidence of such work exists).

---

## Verification (end of task)

- HEAD: `878bd0f9eb5d277510b9b911ecd1a10be0213bd1` — unchanged.
- origin/main: `878bd0f` — unchanged.
- Staged files: **220** (unchanged) — no staging/unstaging performed.
- `package.json` unstaged: **0** in staged set.
- `package-lock.json` unstaged: **0** in staged set.
- No files modified by this investigation except the report: `docs/audit/cline/CARBONTALLY_V3_N8N_PACKAGE_CHANGE_INVESTIGATION.md`.
- No secret values reproduced in this report (the `sk-or-v1-…` string observed in the terminal was a placeholder from an unrelated external prompt echo, not repository content, and is not reproduced here).

**HARD STOP.** No further action performed.
