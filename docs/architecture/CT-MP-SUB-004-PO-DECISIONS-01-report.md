# CT-MP-SUB-004-PO-DECISIONS-01 — Report

| Field | Value |
| --- | --- |
| **Task ID** | `CT-MP-SUB-004-PO-DECISIONS-01` |
| **Date** | 2026-10-04 |
| **Type** | **Documentation + diagnosis only.** No application code, schema, migration, RLS, database, credential or production change. No commit, no push, no deploy. |
| **Repository HEAD** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (`p8-release-reconciled`) |
| **Part A** | Formal PO decision record (PD-1 … PD-6) |
| **Part B** | Platform Admin Demo Lab login diagnostic (diagnosis only — not fixed) |
| **Final status** | **READY FOR PD-5 QA FIXTURE** |

---

## 1. Scope and boundary

This task did two things and nothing else:

* **Part A** — created the formal Product Owner decision record for CT-MP-SUB-004.
* **Part B** — diagnosed why the Product Owner could not sign in as
  `platform.admin@demo-lab.carbontally.local`, **without changing anything**.

### 1.1 Boundary compliance

| Prohibited | Performed? |
| --- | --- |
| Application code change (frontend or backend) | **NO** |
| Database change / data mutation | **NO** |
| Schema / migration change | **NO** |
| RLS change | **NO** |
| Demo Lab data mutation | **NO** |
| Credential reset / password change | **NO** |
| User create / delete | **NO** |
| GoTrue modification | **NO** |
| Frontend auth code change | **NO** |
| Backend auth code change | **NO** |
| Demo Lab seed / reset | **NO** |
| Production access or modification | **NO** |
| Commit / push / deployment | **NO** |
| Reintroducing `:3100` or broadening CORS | **NO** |

### 1.2 Files created by this task

| File | Purpose |
| --- | --- |
| `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` | Part A — the PO decision record |
| `docs/architecture/CT-MP-SUB-004-PO-DECISIONS-01-report.md` | This report |

### 1.3 Files explicitly **not** modified

* `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` — the
  historical independent verification report is **unmodified**; its findings and
  its verdict (**B — "VERIFIED WITH FINDINGS — NOT READY FOR PO ACCEPTANCE"**) are
  **not rewritten**.
* `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md`
  — unmodified (sha256 `a27ad96428808cc44fe632da41dec77c171ed6909cdbbf7bf8e74d676079f3da`,
  identical to the hash recorded by the independent verification).
* `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` —
  unmodified (sha256 `d55644f00ad04014e286597770c57dfff7582bad3fb9523f8729e53e5b29ea5d`,
  identical to the independent verification's recorded hash).

---

## 2. Part A — PO decisions recorded

**PO decision record path:**

```
docs/architecture/CT-MP-SUB-004-PO-decision-record.md
```

**Document ID:** `CT-MP-SUB-004-PODR-01` · **Decision date:** 2026-10-04 ·
**Status:** RATIFIED — PO DECISIONS RECORDED

| # | Decision (verbatim intent) | Options | **PO chose** |
| --- | --- | --- | --- |
| **PD-1** | APPROVE `CT-UX-MP-SUB-003` as the authoritative UI/UX specification; retrospectively authorize the CT-MP-SUB-004 UI implementation against it. | A / B | **A** |
| **PD-2** | Internal CarbonTally staff do **NOT** receive access to the customer Manual Processing route. Keep the current denied/`403` behaviour. | A / B | **A** |
| **PD-3** | **ALL ACTIVE CONSULTANT FIRM MEMBERS** may READ their firm's Manual Processing coverage. `manage_clients` remains required for allocate/release. | A / B | **A** |
| **PD-4** | **KEEP** the existing Admin operational tab label `Manual Processing`. Do not rename it to `Operational Routing`. | A / B | **A** |
| **PD-5** | **CREATE** a deterministic/resettable Demo Lab QA fixture for positive Manual Processing coverage states. (The fixture itself is **not** part of this task.) | A / B | **A** |
| **PD-6** | CT-MP-SUB-003 migrations are architecturally ratified **in principle**, but each migration requires **separate migration review** before being applied to any environment where it is not already applied. **Does NOT authorize production migration/deployment.** | A / B | **B** |

The record contains, for each decision: the option offered, the exact decision,
the rationale/consequence, and its relationship to the independent verification
findings. It further contains two explicit scope-limit statements:

* **PD-6 does NOT authorize production deployment** (migration application remains
  a separately gate-operated PO/ops decision).
* **PD-5 authorizes QA-fixture work ONLY** (no application code, product
  behaviour, schema, migration, RLS, investor-demo, production or deployment change).

### 2.1 Relationship to the independent verification findings F-1 … F-6

| Finding | Severity (per IV report) | Decision relationship |
| --- | --- | --- |
| **F-1** — UI implemented against a non-PO-approved UI/UX specification | HIGH (governance) | **Resolved by PD-1.** This was the stated reason the verdict was not A. |
| **F-2** — inaccurate claim that internal staff keep an exemption on the customer route | LOW | **Addressed by PD-2.** Verified behaviour (`403`) is confirmed as intended; the implementation report's wording remains inaccurate. |
| **F-3** — `ConsultantPage.jsx` diff scope-attribution not verifiable | MEDIUM | **NOT covered by any PD-1…PD-6 decision.** Remains open. |
| **F-4** — incorrect root cause stated for the `App.test.js` failure | LOW | **NOT covered.** Remains a documentation inaccuracy. |
| **F-5** — positive coverage states not browser-verified | MEDIUM | **Remedy authorized by PD-5**; the gap itself remains **OPEN** until the fixture exists and re-verification is performed. |
| **F-6** — Admin operational tab label deviates from spec | MEDIUM / PARTIAL | **Resolved by PD-4** in favour of the implemented label (`Manual Processing`). |

**Note:** PD-3 corresponds to the verification report's §20 **PD-3**, which was
grounded in **F-8 (INFO)** — a finding **outside** the F-1…F-6 severity set. F-8
asked for PO confirmation of the "member-read / capability-write" split; PD-3
provides it. PD-6 corresponds to §20 **PD-6** and has **no direct F-1…F-6**
finding; it is a separate governance gate.

### 2.2 Current CT-MP-SUB-004 acceptance status

**`VERIFIED WITH FINDINGS — NOT YET ACCEPTED`**

* **PD-1 clears the acceptance blocker** created by F-1. The delivered UI is now
  authorized against an approved UI/UX specification, so CT-MP-SUB-004 is **no
  longer blocked on a governance decision**.
* It is **not yet accepted**, because the **F-5 verification gap** (positive
  coverage / capacity / allocate-release / sponsored-direct customer states not
  browser-verified) is still open. PD-5 authorizes the fixture that makes
  re-verification possible.
* Acceptance is therefore now a **verification** step, not a **decision** step.
* The historical IV verdict is **not** amended by this record.

---

## 3. Part B — Platform Admin login diagnostic

**Reported by the Product Owner:**

> "I could not log in as: `platform.admin@demo-lab.carbontally.local`"

**Nature of this part: DIAGNOSIS ONLY.** Nothing was fixed. No user was created
or reset, no password was changed, GoTrue was not modified, no frontend/backend
auth code was touched, no data was written, nothing was seeded and no
credential was mutated.

### 3.1 Methodology

Five evidence channels were used, all read-only or non-mutating:

| # | Channel | What was done |
| --- | --- | --- |
| C1 | **Documentation** | Read `tools/demo_lab/README.md` (§1 topology, §3 authoritative actor list, §7 known limitations) and `tools/demo_lab/manifest.json`. |
| C2 | **Credential source inspection** | Read `~/ct_local_env/demo_lab/credentials.local.json` through a **redacting** walker that printed only structural keys, actor keys, e-mails and user ids — **no password, token, anon key or secret value was emitted**. |
| C3 | **Mechanism inspection** | Read `tools/demo_lab/lab.py` (`demo_password()`), `tools/demo_lab/provision.py` (`ensure_user()`), `tools/demo_lab/lab_env.py`. |
| C4 | **Runtime existence / state check (read-only)** | Password-grant `POST /auth/v1/token?grant_type=password` against the local Demo Lab gateway `http://127.0.0.1:54430` for the reported actor plus two control actors. Only the **HTTP status**, `user_id`, `email_confirmed_at` and `banned_until` were read; **no token was printed**. |
| C5 | **Historical log correlation** | Grepped `~/ct_local_env/demo_lab/backend.log` for the actor's e-mail and for auth-failure signatures; checked container uptimes and state-file mtimes. |

**Side effect disclosure (transparency):** a successful password-grant creates the
ordinary Supabase auth **session** record that any login creates — local Demo Lab
GoTrue only, ephemeral, no credential/user change. This is the same side effect
as the Product Owner's own login attempts. No password, user, role or credential
was created, modified or deleted.

---

## 4. Actor / e-mail mapping

### 4.1 The reported actor

| Property | Value | Source |
| --- | --- | --- |
| Actor key | `platform_admin` | `manifest.json`, `credentials.local.json` |
| E-mail (reported) | `platform.admin@demo-lab.carbontally.local` | PO report |
| E-mail (registered) | `platform.admin@demo-lab.carbontally.local` | `credentials.local.json` → `actors.platform_admin.email` |
| Local part | `platform.admin` | `manifest.json` → `local_part` |
| Auth user id | `1fe17efb-4565-40ab-9fba-115db13fc111` | `credentials.local.json`; confirmed live (C4) |
| Entity | `platform` (CarbonTally internal) | `manifest.json` → `entity` |
| Staff role | `admin` (`can_manage_organizations`) | `manifest.json` → `staff_role`; `README.md` §3 |
| Expected destination | `/ops` | `manifest.json` → `expect.destination`; `~/ct_local_env/pw_verify.py` `EXPECTED` map |
| E-mail domain | `demo-lab.carbontally.local` | `README.md` §3 |

**The two e-mails are byte-identical.** The Product Owner's supplied address is
the exact registered address.

### 4.2 Other Demo Lab staff actors (context)

For completeness, the Demo Lab has **14** actors under the shared domain
`demo-lab.carbontally.local`, of which the internal-staff actors are:

| Actor key | E-mail | Destination |
| --- | --- | --- |
| `platform_admin` | `platform.admin@demo-lab.carbontally.local` | `/ops` |
| `internal_operator` | `operator@demo-lab.carbontally.local` | `/ops` |
| `pe_manager` | `pe.manager@demo-lab.carbontally.local` | `/pe` |
| `pe_beta_manager` | `pe.beta.manager@demo-lab.carbontally.local` | `/pe` |

(plus four Org-A roles, two Org-B roles, two consultant-firm roles and two
consultant-client owners.)

---

## 5. Is the supplied e-mail a valid Demo Lab actor?

### **YES — the supplied e-mail is a valid, correctly-registered Demo Lab actor.**

| Question | Answer |
| --- | --- |
| Does the exact e-mail exist in the generated local credentials? | **YES** — `credentials.local.json` → `actors.platform_admin.email` |
| Is it the actor the PO meant (`platform_admin`)? | **YES** — actor key `platform_admin`, staff role `admin`, destination `/ops` |
| Does a GoTrue auth user exist for it? | **YES** — user id `1fe17efb-4565-40ab-9fba-115db13fc111` |
| Is the e-mail confirmed? | **YES** — `email_confirmed_at = 2026-10-04T13:13:32.430027Z` |
| Is the account suspended / banned? | **NO** — `banned_until = None` |
| Does a valid credential authenticate it **right now**? | **YES** — `HTTP 200` on a password grant |

### 5.1 Live verification result (read-only; no token printed)

| Actor | E-mail | Result | Auth user id | `email_confirmed_at` | `banned_until` |
| --- | --- | --- | --- | --- | --- |
| `platform_admin` | `platform.admin@demo-lab.carbontally.local` | **HTTP 200** | `1fe17efb-4565-40ab-9fba-115db13fc111` | `2026-10-04T13:13:32Z` | `None` |
| `internal_operator` (control) | `operator@demo-lab.carbontally.local` | HTTP 200 | `960649a6-8fc3-4418-8b21-dbf69eec3652` | `2026-10-04T13:13:32Z` | `None` |
| `consultant_owner` (control) | `consultant.owner@demo-lab.carbontally.local` | HTTP 200 | `304ff83c-dd57-40d2-8032-b5de3f6eb86a` | `2026-10-04T13:13:33Z` | `None` |

**Conclusion:** the Demo Lab Platform Admin identity is **healthy and
authenticating**. Therefore the login problem is **NOT**:

* ❌ a wrong actor mapping,
* ❌ an absent auth user,
* ❌ an unconfirmed e-mail,
* ❌ a suspended/banned account,
* ❌ a broken or non-existent Platform Admin e-mail address.

### 5.2 How the credential is generated (mechanism)

From `tools/demo_lab/lab.py`:

```python
def demo_password() -> str:
    """A lab-specific synthetic password (never a production credential)."""
    state = load_state()
    if not state.get("demo_password"):
        state["demo_password"] = "Lab-" + secrets.token_urlsafe(18)
        save_state(state)
    return state["demo_password"]
```

From `tools/demo_lab/provision.py` (`ensure_user`): for an e-mail that already
exists in GoTrue, provisioning issues an **update** whose body is
`{"password": password, "email_confirm": True}` — i.e. **every provisioning run
re-asserts the same state password for every actor**.

Consequences of this mechanism:

1. **All 14 Demo Lab actors share ONE password**, stored as `demo_password` in
   `~/ct_local_env/demo_lab/credentials.local.json`. There is no per-actor
   password, so "the Platform Admin password" and "the lab password" are the
   same value.
2. The password is **stable across re-runs** as long as the state file survives.
3. The password **rotates only** if the state file is removed — e.g.
   `./tools/demo_lab/reset_demo_lab.sh --purge-state` (documented in
   `README.md` §2 as "*also delete local credentials/evidence*") — or if a
   different `DEMO_LAB_STATE_DIR` is used.
4. `provision.py` mirrors the 13 lab user ids into the lab database's
   `auth.users` (ids and e-mails only — no hashes, no sessions), so the lab
   database's own `auth` mirror carries **no usable password**; authentication
   always happens at the gateway's GoTrue.

### 5.3 Stack re-provisioning observed on 2026-10-04

| Artefact | Timestamp (local, +0600) |
| --- | --- |
| `carbontally_demo_lab_storage` container created | 2026-10-04 19:13:22 |
| `credentials.local.json` written | 2026-10-04 19:13:37 |
| `backend.env` written | 2026-10-04 19:13:38 |
| `generated/nginx.conf` written | 2026-10-04 19:13 |
| All three probed users' `email_confirmed_at` | 2026-10-04 13:13:32–33 **UTC** (= 19:13:32–33 local) |
| `carbontally_demo_lab_gateway` container | created 2026-10-03 20:14 (**not** recreated) |

So the Demo Lab identities were **(re)written at 2026-10-04 19:13 local time**,
while the gateway itself has been continuously up for ~24 h and the PostgREST
container for ~5 days. The previous successful browser verification of
`platform_admin` occurred **after** that re-provisioning (see §6.1).

---

## 6. Root cause of the login problem

Because the identity, the auth user, the account state and a valid credential
were **all proven good** (§5), the failure cannot be attributed to the Demo Lab
Platform Admin actor itself. The determinable root causes, in order of
likelihood, are:

### RC-1 (most probable) — the sign-in was attempted from the **wrong origin** (`:3100`)

The Demo Lab's CORS allow-list, its GoTrue site URL and the backend's
`ALLOWED_ORIGINS` all align on **`http://localhost:3000`**. The `:3100` origin is
**not** allowed, so the browser blocks the auth call and the UI reports a sign-in
failure even though the credentials are perfectly valid.

Supporting evidence:

* The previously running dev server was **still bound to `:3100`**, and
  `frontend/.env.local` still carries `PORT=3100` (its header comment even reads
  *"ISOLATED LOCAL ENV for 93d5cdd (setup task 072)"*).
* `~/ct_local_env/README.md` documents the frontend as
  *"Frontend `http://localhost:3100`"*, which is a **different environment's**
  documented origin — a plausible source of the wrong URL.
* The prior CT-MP-SUB-004-LOCAL-FRONTEND-02 investigation recorded exactly this:
  sign-in succeeds on `:3000` and fails on `:3100` for the same credentials, and
  classified it as the **documented DR-003 §21.3 origin mismatch — not an
  application defect**.
* Sign-in for **this exact actor** on `:3000` was verified successful.

### RC-2 — the password used came from a **different local identity universe**

Three unrelated local identity systems exist on this machine, with **different
e-mail domains and different credential mechanisms**:

| System | E-mail domain | How you log in | Can a password login work? |
| --- | --- | --- | --- |
| **Demo Lab** (`tools/demo_lab/`) | `@demo-lab.carbontally.local` | shared `demo_password` in `~/ct_local_env/demo_lab/credentials.local.json` | **YES** |
| Isolated env for `93d5cdd` (setup task 072) | `@local.test` (`local-owner@local.test`, …) | pre-minted HS256 tokens listed in `~/ct_local_env/IDENTITIES.md` | **NO** — no passwords exist; `~/ct_local_env/README.md` states Supabase is deliberately pointed at an unroutable placeholder (`http://127.0.0.1:19999`) |
| Investor demo dataset | `@demo.carbontally.local` | separate demo credential mechanism | not applicable to the Demo Lab gateway |

A password copied from either of the latter two universes **cannot** authenticate
against the Demo Lab gateway. The misleading `frontend/.env.local` header comment
("ISOLATED LOCAL ENV for 93d5cdd (setup task 072)") makes this confusion easy to
make, because that same file actually points `REACT_APP_SUPABASE_URL` at the
**Demo Lab** gateway (`http://127.0.0.1:54430`).

### RC-3 — a **stale** password captured before the 2026-10-04 19:13 re-provisioning

If the Demo Lab state directory was purged (`reset_demo_lab.sh --purge-state`) at
some point, `demo_password()` would have minted a **new** `Lab-…` value at the
next provisioning run. A password noted from an earlier session would then be
stale and rejected.

**Honest limitation:** the available evidence **cannot prove** whether the
password rotated at 19:13:37 (the state file is rewritten on every provisioning
run, so its mtime alone is not proof of rotation). RC-3 is therefore recorded as
a *possible* contributing cause, not a confirmed one.

### 6.1 Definitive ruling: causes RULED OUT

| Candidate cause | Verdict | Evidence |
| --- | --- | --- |
| Wrong actor mapping | **RULED OUT** | `platform_admin` ↔ the exact e-mail is registered in `manifest.json` and `credentials.local.json` |
| Auth-user absence | **RULED OUT** | Live `HTTP 200`; user id `1fe17efb-…` |
| Unconfirmed e-mail | **RULED OUT** | `email_confirmed_at = 2026-10-04T13:13:32Z` |
| Account state (banned/suspended) | **RULED OUT** | `banned_until = None` |
| The e-mail "does not exist" | **RULED OUT** | It exists verbatim |
| Credential invalid | **RULED OUT** | A valid password grant succeeds |
| Gateway / GoTrue down | **RULED OUT** | Gateway up ~24 h; auth health and token grants succeed |

### 6.2 Confirmation — did the earlier successful `platform_admin` verification use a different e-mail?

**NO. It used the SAME e-mail identity.**

`~/ct_local_env/demo_lab/backend.log` shows the backend successfully
authenticating this actor:

```
✅ User authenticated: platform.admin@demo-lab.carbontally.local (ID: 1fe17efb-4565-40ab-9fba-115db13fc111)
✅ Found staff profile for user: platform.admin@demo-lab.carbontally.local
ℹ️ User platform.admin@demo-lab.carbontally.local is not an active organization member
```

These entries correspond to the earlier successful browser verification of
`platform_admin` → `/ops` (the *"not an active organization member"* line is the
expected F-2 behaviour confirmed by **PD-2**, not an error). The successful
verification therefore used **`platform.admin@demo-lab.carbontally.local`** —
byte-identical to the address the Product Owner reports failing.

**This is the decisive finding: the identical address authenticated successfully
from one origin and failed for the Product Owner.** That asymmetry points to the
**environment/origin** or the **credential source**, not to the identity.

---

## 7. Root cause summary

| Aspect | Determination |
| --- | --- |
| Is `platform.admin@demo-lab.carbontally.local` a valid Demo Lab actor? | **YES** (§5) |
| Are the credentials valid? | **YES** — `HTTP 200` (§5.1) |
| Cause | **Environmental / credential-source, not identity.** Most probable: **wrong origin (`:3100`)**, where Demo Lab CORS blocks the auth call (RC-1). Also possible: a password taken from a different local identity universe (RC-2) or a stale password captured before the 2026-10-04 19:13 re-provisioning (RC-3). |
| Confidence | **HIGH** that the actor and credential are correct; **MODERATE** on which of RC-1 / RC-2 / RC-3 applied, because the Product Owner's origin and typed password were not observable in this session. |
| Application defect? | **NO.** No application defect was found. The Demo Lab origin/CORS configuration is documented behaviour (DR-003 §21.3). |

---

## 8. Exact safe action for the Product Owner

**No change was made to make the login work. The following action is
non-mutating and requires no code, data or credential change.**

### Step 1 — use the correct origin

Open the Demo Lab frontend at:

```
http://localhost:3000
```

**Do NOT use `http://localhost:3100`.** `:3000` is the origin the Demo Lab
gateway, its GoTrue site URL and the backend `ALLOWED_ORIGINS` are all
configured for. Sign-in on `:3100` is blocked by CORS and *appears* as a login
failure (documented DR-003 §21.3).

### Step 2 — use the correct e-mail

```
platform.admin@demo-lab.carbontally.local
```

### Step 3 — use the Demo Lab lab password (the one stored with the lab credentials)

All 14 Demo Lab actors share **one** password, stored as the `demo_password`
field of:

```
~/ct_local_env/demo_lab/credentials.local.json
```

To display it in your own terminal (nothing is written, nothing is changed):

```bash
python3 -c "import json,os;print(json.load(open(os.path.expanduser('~/ct_local_env/demo_lab/credentials.local.json')))['demo_password'])"
```

> ⚠️ This prints a **local lab credential** to your terminal only. It is a
> synthetic Demo Lab password, **never** a production credential. Do not paste it
> into reports, tickets, commits or chat.

### Step 4 — expect the Platform Admin destination

After a successful sign-in, the Platform Admin actor lands on **`/ops`** (the
Admin control plane) — per `manifest.json` (`expect.destination = /ops`) and the
`EXPECTED` map in `~/ct_local_env/pw_verify.py`.

### Step 5 — if Step 1–3 still fail

Do **not** reset the Demo Lab. Instead capture the browser **Network** entry for
the `POST …/auth/v1/token?grant_type=password` request:

* A **CORS / blocked** failure ⇒ you are still on the wrong origin (return to Step 1).
* **`400 invalid_grant` / "Invalid login credentials"** ⇒ the password value is
  wrong (re-read Step 3); do not reset data.
* **User not found** ⇒ the wrong e-mail domain was used (`@demo.carbontally.local`
  or `@local.test` instead of `@demo-lab.carbontally.local`).

### Do NOT do

* Do **not** use the `local-*@local.test` identities from
  `~/ct_local_env/IDENTITIES.md` — that environment issues **tokens, not
  passwords**, and points Supabase at an unroutable placeholder, so a password
  login there can never succeed.
* Do **not** reuse the investor-demo (`@demo.carbontally.local`) password.
* Do **not** run `reset_demo_lab.sh` / `--purge-state` to "fix" a login — that
  would destroy legitimate Demo Lab state and rotate the lab password.
* Do **not** use `:3100` or broaden CORS.

If `:3100` support is genuinely wanted, that is a **separate, bounded
configuration task** (resolve DR-003 §21.3) and is explicitly out of scope here.

---

## 9. Files and configuration inspected

**Read-only inspection only. Nothing below was modified.**

| Path | Why inspected |
| --- | --- |
| `tools/demo_lab/README.md` | Authoritative actor list (§3), topology (§1), known limitations (§7), credential/reset commands (§2) |
| `tools/demo_lab/manifest.json` | Authoritative actor definition for `platform_admin` (`local_part`, `entity`, `staff_role`, `expect`) |
| `tools/demo_lab/lab.py` | `demo_password()` generation; state-file location (`STATE_DIR`, `CREDENTIALS_PATH`) |
| `tools/demo_lab/provision.py` | `ensure_user()` password/`email_confirm` semantics; `list_users()` admin enumeration |
| `tools/demo_lab/lab_env.py` | How `backend.env` (DB URL + gateway URL) is rendered |
| `~/ct_local_env/demo_lab/credentials.local.json` | Actor ↔ e-mail ↔ user-id mapping (**redacted inspection**; no secret values emitted) |
| `~/ct_local_env/demo_lab/backend.log` | Historical successful authentication of the actor; auth-failure signatures |
| `~/ct_local_env/demo_lab/backend.env` | Gateway/DB wiring (mtime correlation only) |
| `~/ct_local_env/README.md` | The `:3100` documented origin and the unroutable-placeholder limitation that explain RC-1/RC-2 |
| `~/ct_local_env/IDENTITIES.md` | The competing `local-*@local.test` identity universe (e-mails only) |
| `~/ct_local_env/pw_verify.py` | Authoritative actor→destination `EXPECTED` map; confirms it reads `["actors"]` + `["demo_password"]` |
| `frontend/.env.local` | Confirms `PORT=3100` (stale origin) and `REACT_APP_SUPABASE_URL=http://127.0.0.1:54430` (Demo Lab gateway) |
| `docs/architecture/CT-MP-SUB-004-independent-verification-report.md` | F-1…F-6, §19 NV list, §20 PD list, §21 verdict |
| `docs/architecture/CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` | On-face status marker; sha256 baseline |
| `docs/architecture/CarbonTally_Manual_Processing_Subscription_Options.md` | sha256 baseline |
| `supabase/migrations/` | Confirmation the three PD-6 migrations exist (`20261010000000_…`, `20261030000000_…`, `20261101000000_…`) |

### 9.1 Runtime state observed (read-only)

* `carbontally_demo_lab_gateway` — up ~24 h (created 2026-10-03 20:14 +0600)
* `carbontally_demo_lab_postgrest` — up ~5 days (created 2026-09-24 16:14 +0600)
* `carbontally_demo_lab_storage` — created 2026-10-04 19:13:22 +0600
* Local Demo Lab gateway reachable at `http://127.0.0.1:54430`

---

## 10. Safety confirmations

| Requirement | Confirmation |
| --- | --- |
| **No credentials / secrets exposed** | **CONFIRMED.** No password, access token, refresh token, JWT secret, anon key, service key, or signed URL appears in this report or in the PO decision record. The credentials file was read through a redacting walker that printed only structural keys, actor keys, e-mails and user ids. Token values returned by the read-only auth probe were explicitly **not** printed — only `HTTP 200`, `user_id`, `email_confirmed_at` and `banned_until` were read. |
| **No state changed** | **CONFIRMED.** No user created/deleted; no password set/changed/reset; no GoTrue change; no frontend or backend auth-code change; no database write; no schema/migration/RLS change; no Demo Lab seed or reset. The **only** side effect is the ordinary ephemeral GoTrue **session** record inherent to any password-grant (same as the PO's own login attempt); no credential, user or role was altered. |
| **No production accessed** | **CONFIRMED.** No production host, Supabase project, API, database or storage was contacted. All runtime checks were against the local Demo Lab gateway on `127.0.0.1:54430`. |
| **No commit / push / deploy** | **CONFIRMED.** `HEAD` unchanged at `375a48dc1b9e9cfd74090bbf747554ae997acb59`. |
| **Historical IV report unaltered** | **CONFIRMED.** sha256 `128c47cfc94fafc9931a0fb38dd964e359e9becd53d3ae0a35109587870748f9` (unmodified). |
| **PD-5 NOT implemented** | **CONFIRMED.** No QA fixture was created. |
| **PD-6 migrations NOT applied** | **CONFIRMED.** No migration was run against any environment. |
| **`:3100` not reintroduced / CORS not broadened** | **CONFIRMED.** No configuration was changed; `:3000` remains the documented origin. |

---

## 11. Remaining work

| # | Remaining item | Owner | Notes |
| --- | --- | --- | --- |
| R-1 | **Implement the PD-5 Demo Lab QA fixture** (deterministic, resettable) for positive Manual Processing coverage states | Cline (new bounded task) | **Authorized** by PD-5; **not** performed here. Must respect AGENTS.md §55 (isolated, labelled, tracked, cleaned up). |
| R-2 | **Re-verify** the positive states in a real browser once R-1 exists (consultant capacity meter + covered-clients, allocate/release, populated ALL_ELIGIBLE_CLIENTS, customer available/direct/sponsored/direct+sponsored) | Independent QA | Closes **F-5** and **NV-1…NV-4, NV-8** — the last open gate on CT-MP-SUB-004 acceptance. |
| R-3 | Update the now-stale governance markers in `CT-UX-MP-SUB-003` (`Status: PROPOSED FOR PO APPROVAL`; §11 `UI implementation — NOT YET AUTHORIZED`) to reflect PD-1 | Documentation task | The specification was **deliberately not edited** in this task (out of scope). Until updated, the spec's own face contradicts PD-1. |
| R-4 | Resolve **F-3** (scope attribution of the two reworded `consultantUploadError` strings in `ConsultantPage.jsx`) or have the PO explicitly waive it | Independent QA / PO | Not covered by any PD-1…PD-6 decision. |
| R-5 | Correct the two inaccurate claims in `CT-MP-SUB-004-implementation-report.md` (**F-2** internal-staff exemption wording; **F-4** `react-router/dom` root cause) | Documentation task | LOW; report wording only. |
| R-6 | Each of the three PD-6 migrations requires its **own migration review** before being applied to any environment where it is not already applied | PO / ops gate | PD-6 explicitly does **not** authorize production migration/deployment. |
| R-7 | Optionally resolve **DR-003 §21.3** if `:3100` support is genuinely wanted | Separate bounded task | Out of scope here; `:3000` is the supported Demo Lab origin. |
| R-8 | PD-7 (final public pricing, payment provider) remains **OPEN** | PO | Carried forward from D1 §29; unaffected by PD-1…PD-6. |
| R-9 | Optionally stop the stale `:3100` dev server to remove the origin-confusion hazard that most likely caused the PO's login failure | Local ops | Optional housekeeping; not required. |

---

## 12. Final status

> # ✅ **READY FOR PD-5 QA FIXTURE**

**Justification:**

1. **Part A complete.** The formal PO decision record exists at
   `docs/architecture/CT-MP-SUB-004-PO-decision-record.md` (Document ID
   `CT-MP-SUB-004-PODR-01`), recording PD-1 … PD-6 with exact decisions,
   rationale/consequences, relationships to findings F-1…F-6, the explicit
   statement that **PD-6 does not authorize production deployment**, the explicit
   statement that **PD-5 authorizes QA-fixture work only**, and the current
   CT-MP-SUB-004 acceptance status. The historical independent verification
   report was **not** altered and its verdict was **not** rewritten.
2. **Part B complete.** The Platform Admin login issue is **diagnosed, not
   fixed**. `platform.admin@demo-lab.carbontally.local` is a **valid Demo Lab
   actor** with a **valid, working credential** (`HTTP 200`), confirmed
   un-banned and e-mail-confirmed. The earlier successful `platform_admin`
   browser verification used the **same** e-mail. The failure is attributed to
   **environment / credential-source** causes (most probably the wrong `:3100`
   origin), with a safe, non-mutating login instruction provided.
3. **No blocker for PD-5.** The login problem does **not** block the PD-5 QA
   fixture work: the Platform Admin actor used for the existing verification is
   healthy, the CT-MP-SUB-004 surfaces were previously reached, and the DO-NOT
   list in §8 prevents the destructive "fixes" that would otherwise be tempting.

**No part of PD-5 and no part of PD-6 was implemented in this task.**

---

*Companion record:* `docs/architecture/CT-MP-SUB-004-PO-decision-record.md`
*Historical (unmodified):* `docs/architecture/CT-MP-SUB-004-independent-verification-report.md`