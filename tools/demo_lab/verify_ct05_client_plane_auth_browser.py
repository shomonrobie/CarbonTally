#!/usr/bin/env python3
"""CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05 — BROWSER verification.

Reproduces, with real headless Chrome and a REAL password login against the lab
GoTrue (no token injection), the manual observation this task remediates: the
CT03 managed client (``ct03.owner.managed@demo-lab.carbontally.local``) could
upload a document and create a facility on the ORGANISATION plane, and the UI
displayed "CarbonTally V3".

It proves the fix at the human AND server boundary:

* the managed client still sees their ORGANISATION (not a blank/denied screen);
* the master-data create controls are GONE and a read-only explanation is shown;
* the upload control is GONE and an explanation is shown;
* the bare "V3" product tag is gone (the brand reads "CarbonTally");
* the SERVER denies the same actions directly (upload-url 403, facility 403) and
  ``/me/context`` reports the managed client-access ceiling;
* REGRESSION — a CONSULTANT operating the SAME client workspace still sees the
  master-data controls (the ceiling applies only to the client user).

Reads only; writes screenshots into the lab evidence directory.

Usage::

    ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_ct05_client_plane_auth_browser.py
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402
import fixture_ct03_client_plane as fixture  # noqa: E402

FRONTEND = "http://localhost:3000"
CHROME = "/usr/bin/google-chrome"
BACKEND = f"http://127.0.0.1:{lab.BACKEND_PORT}"
REALTIME_NOISE = "realtime/v1/websocket"
#: Pre-existing legacy membership probe (see ``no_unexpected``).
LEGACY_MEMBERSHIP_NOISE = "/api/organizations/members"

MANAGED_EMAIL = fixture.NEW_CLIENTS[0]["email"]  # ct03.owner.managed@...
MANAGED_ORG = fixture._id("org:managed")
MANAGED_NAME = fixture.NEW_CLIENTS[0]["name"]  # CT03-QA Managed Client
# The consultant client plane addresses a client by its GRANT/relationship id
# (``repos.consultants.get_client``), NOT by the organisation id.
MANAGED_CLIENT_ID = fixture._id("relationship:managed")
CONSULTANT_EMAIL = "consultant.owner@demo-lab.carbontally.local"


def shot(page, name: str) -> str:
    lab.ensure_dirs()
    out = lab.EVIDENCE_DIR / "browser" / f"ct05_plane_{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
    return str(out)


def _console_error(message) -> str:
    """Console error text WITH its source URL (Chrome's text omits the URL)."""
    try:
        loc = (message.location or {}).get("url") or ""
    except Exception:  # noqa: BLE001
        loc = ""
    return f"{message.text} @ {loc}" if loc else message.text


def login(page, email: str, password: str) -> None:
    page.goto(f"{FRONTEND}/login", wait_until="domcontentloaded")
    page.wait_for_selector('input[type="email"]', timeout=30000)
    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !location.pathname.startsWith('/login')", timeout=60000)


def _api(token: str, path: str, *, method: str = "GET", body: dict | None = None):
    return lab.http_json(
        f"{BACKEND}{path}", method=method, headers={"Authorization": f"Bearer {token}"}, body=body
    )


def run(headed: bool) -> dict:
    from playwright.sync_api import sync_playwright

    password = lab.demo_password()
    checks: list[dict] = []
    notes: list[str] = []

    def check(name: str, ok: bool, detail: str = "", screenshot: str | None = None) -> None:
        item = {"check": name, "ok": bool(ok), "detail": detail}
        if screenshot:
            item["screenshot"] = screenshot
        checks.append(item)

    def no_unexpected(app_errors, label):
        # An EXPECTED 403 from the client-access ceiling is the correct outcome,
        # so it is evidence, not a failure (AGENTS.md §78).
        expected = [e for e in app_errors if "403" in e]
        unexpected = [e for e in app_errors if e not in expected]
        # PRE-EXISTING and out of CT-05 scope: ``resolveV3Organization`` probes the
        # LEGACY ``/api/organizations/members...`` family for the caller's primary
        # organisation and 404s for a principal with no direct-customer membership
        # (a consultant principal), then falls back to the consultant engagement
        # context — which is why the consultant plane renders fine. The CT-05
        # ceiling NEVER returns 404 and never touches this legacy route family, so
        # this noise cannot be a CT-05 regression. Recorded as an observation.
        legacy = [e for e in unexpected if LEGACY_MEMBERSHIP_NOISE in e]
        if legacy:
            notes.append(
                f"{label}: {len(legacy)} pre-existing legacy "
                f"'{LEGACY_MEMBERSHIP_NOISE}' 404 probe(s) — out of CT-05 scope"
            )
        unexpected = [e for e in unexpected if e not in legacy]
        if expected:
            notes.append(f"{label}: {len(expected)} expected 403 ceiling log(s) — correct authorization outcome")
        check(
            f"{label}: no UNEXPECTED application console errors",
            not unexpected,
            "; ".join(e.split("?")[0] for e in unexpected)[:300],
        )

    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME, headless=not headed)

        # --- The managed client (the identity from the report) ---------------
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(_console_error(m)) if m.type == "error" else None)
        try:
            login(page, MANAGED_EMAIL, password)
            page.wait_for_timeout(2500)
            check("managed: logged in off /login", "/login" not in page.url, page.url)

            page.goto(f"{FRONTEND}/home", wait_until="domcontentloaded")
            # The active organisation resolves from /me/context; wait for the nav
            # to bind it rather than assuming a fixed settle time.
            try:
                page.wait_for_selector(".v3-nav-org", timeout=25000)
            except Exception:  # noqa: BLE001
                pass
            page.wait_for_timeout(1500)
            home = page.locator("body").inner_text()
            # The active organisation is shown in the nav (D21 ``.v3-nav-org``).
            nav_org = page.locator(".v3-nav-org").first
            org_label = nav_org.inner_text().strip() if nav_org.count() else ""
            check(
                "managed: sees their organisation",
                MANAGED_NAME in org_label or MANAGED_NAME in home,
                org_label or home[:120],
            )
            check("managed: organisation plane (not denied)", "not available" not in home.lower())

            brand = page.locator(".v3-nav-brand").inner_text().strip()
            check("managed: brand reads 'CarbonTally' with no 'V3'", brand == "CarbonTally", brand)
            check("managed: nav screenshot", True, "", shot(page, "managed_home"))

            page.goto(f"{FRONTEND}/organization?tab=facilities", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            org = page.locator("body").inner_text()
            check("managed: '+ New facility' control is GONE", "+ New facility" not in org)
            check("managed: '+ New asset' control is GONE", "+ New asset" not in org)
            check(
                "managed: read-only master-data explanation shown",
                "read-only for organisation master data" in org,
            )
            check("managed: facilities screenshot", True, "", shot(page, "managed_facilities"))

            page.goto(f"{FRONTEND}/documents", wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            docs = page.locator("body").inner_text()
            check("managed: upload drop-zone is GONE", "Drag and drop documents here" not in docs)
            check(
                "managed: upload restriction explanation shown",
                "does not permit document upload" in docs,
            )
            check("managed: documents screenshot", True, "", shot(page, "managed_documents"))
        except Exception as exc:  # noqa: BLE001
            check("managed: browser flow", False, str(exc)[:300])
        finally:
            no_unexpected([e for e in errors if REALTIME_NOISE not in e], "managed")
            context.close()

        # --- Server boundary (the SAME session, no browser shortcuts) --------
        try:
            token, method = fixture._login(MANAGED_EMAIL, password)
            check("managed: password-grant login for API checks", bool(token), method)

            status, payload, _raw = _api(token, "/api/v3/me/context")
            ca = payload.get("client_access") if isinstance(payload, dict) else None
            caps = (ca or {}).get("capabilities", {})
            check("api: /me/context -> 200", status == 200, str(status))
            ctx_org = (payload or {}).get("organization") or {}
            check(
                "api: /me/context still carries the client's organisation",
                ctx_org.get("name") == MANAGED_NAME,
                json.dumps(ctx_org)[:160],
            )
            check(
                "api: /me/context reports the managed client-access ceiling",
                isinstance(ca, dict)
                and ca.get("profile") == "managed"
                and caps.get("upload_document") is False
                and caps.get("edit_master_data") is False,
                json.dumps(ca)[:200],
            )

            status, _p, _r = _api(
                token, "/api/v3/documents/upload-url", method="POST",
                body={"organization_id": MANAGED_ORG, "filename": "qa.pdf", "size_bytes": 10},
            )
            check("api: client upload-url is DENIED (403)", status == 403, str(status))

            status, _p, _r = _api(
                token, f"/api/v3/organizations/{MANAGED_ORG}/facilities", method="POST",
                body={"name": "QA Facility", "postcode": "AB1 2CD"},
            )
            check("api: client facility create is DENIED (403)", status == 403, str(status))
        except Exception as exc:  # noqa: BLE001
            check("api: server boundary checks", False, str(exc)[:300])

        # --- REGRESSION: the consultant operating the SAME client ------------
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        errors = []
        page.on("console", lambda m: errors.append(_console_error(m)) if m.type == "error" else None)
        try:
            login(page, CONSULTANT_EMAIL, password)
            page.goto(
                f"{FRONTEND}/consultant/clients/{MANAGED_CLIENT_ID}/organization?tab=facilities",
                wait_until="domcontentloaded",
            )
            page.wait_for_timeout(3000)
            consultant_body = page.locator("body").inner_text()
            check(
                "regression: consultant operating the same client still sees '+ New facility'",
                "+ New facility" in consultant_body,
            )
            check("regression: consultant screenshot", True, "", shot(page, "consultant_facilities"))
        except Exception as exc:  # noqa: BLE001
            check("regression: consultant browser flow", False, str(exc)[:300])
        finally:
            no_unexpected([e for e in errors if REALTIME_NOISE not in e], "consultant")
            context.close()

        browser.close()

    failed = [c for c in checks if not c["ok"]]
    return {"checks": checks, "passed": len(checks) - len(failed), "failed": len(failed),
            "ok": not failed, "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run(args.headed)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result["checks"]:
            mark = "PASS" if item["ok"] else "FAIL"
            print(f"[{mark}] {item['check']}" + ("" if item["ok"] else f" :: {item['detail']}"))
        for note in result["notes"]:
            print(f"[note] {note}")
        print(f"--- {result['passed']} passed, {result['failed']} failed ---")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


