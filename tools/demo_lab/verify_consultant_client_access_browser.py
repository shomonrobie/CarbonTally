#!/usr/bin/env python3
"""CT-CONSULTANT-CLIENT-ACCESS-UX-01 — BROWSER verification.

Drives the REAL frontend at http://localhost:3000 with real headless Chrome and a
REAL password login against the lab GoTrue (no token injection). It proves the
human contract this task fixes:

* the consultant client operating plane now presents a **Client Access** tab
  (NOT "Members & Invitations") — CoStrict F3 closure;
* the primary CTA is **"+ Invite Client"**;
* the invite form is **email + client access level** only (no raw user id);
* the sent invitation appears under **Pending Invitations** and is then REVOKED
  as cleanup (isolated, clearly-labelled QA record — AGENTS.md §55);
* the consultant plane exposes **no** invitation token / accept link / Copy link;
* the DIRECT customer plane still uses **"Members & Invitations"** (unchanged).

Reads only; writes screenshots into the lab evidence directory and one clearly
labelled QA invitation which it revokes before exiting.

Usage::

    ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_consultant_client_access_browser.py
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import secrets
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

FRONTEND = "http://localhost:3000"
CHROME = "/usr/bin/google-chrome"
REALTIME_NOISE = "realtime/v1/websocket"
CONSULTANT_EMAIL = "consultant.owner@demo-lab.carbontally.local"
CUSTOMER_EMAIL = "owner.clienta@demo-lab.carbontally.local"
QA_EMAIL = f"ct-access-qa+{secrets.token_hex(4)}@demo-lab.carbontally.local"


def shot(page, name: str) -> str:
    lab.ensure_dirs()
    out = lab.EVIDENCE_DIR / "browser" / f"ct_client_access_{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
    return str(out)


def login(page, email: str, password: str) -> None:
    page.goto(f"{FRONTEND}/login", wait_until="domcontentloaded")
    page.wait_for_selector('input[type="email"]', timeout=30000)
    page.fill('input[type="email"]', email)
    page.fill('input[type="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !location.pathname.startsWith('/login')", timeout=60000)


def _open_managed_client(page) -> str | None:
    """From the consultant plane, open the first managed client workspace."""
    page.goto(f"{FRONTEND}/consultant", wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    page.get_by_role("button", name="Clients", exact=True).click()
    page.wait_for_timeout(1200)
    open_btn = page.get_by_role("button", name="Open workspace").first
    if open_btn.count() == 0:
        return None
    open_btn.click()
    page.wait_for_timeout(3000)
    m = re.search(r"/consultant/clients/([^/]+)/", page.url)
    return m.group(1) if m else None


def run() -> dict:
    from playwright.sync_api import sync_playwright

    password = lab.demo_password()
    checks: list[dict] = []
    notes: list[str] = []

    def check(name: str, ok: bool, detail: str = "", screenshot: str | None = None) -> None:
        item = {"check": name, "ok": bool(ok), "detail": detail}
        if screenshot:
            item["screenshot"] = screenshot
        checks.append(item)

    with sync_playwright() as play:
        browser = play.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        errors: list[str] = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        try:
            login(page, CONSULTANT_EMAIL, password)
            client_id = _open_managed_client(page)
            check("consultant: managed client opened", bool(client_id), page.url)

            if client_id:
                page.goto(
                    f"{FRONTEND}/consultant/clients/{client_id}/organization",
                    wait_until="domcontentloaded",
                )
                page.wait_for_timeout(3000)

                # --- the members surface is now the consultant "Client Access" -----
                check("client_plane: 'Client Access' tab present",
                      page.get_by_role("button", name="Client Access").count() == 1)
                check("client_plane: NO 'Members & Invitations' tab",
                      page.get_by_role("button", name="Members & Invitations").count() == 0)

                page.get_by_role("button", name="Client Access").first.click()
                page.wait_for_timeout(2000)
                body = page.locator("body").inner_text()
                check("client_plane: Client Access heading rendered", "Client Access" in body)
                check("client_plane: purpose copy rendered",
                      "invite your client to access their carbontally dashboard"
                      in body.lower())
                check("client_plane: primary CTA '+ Invite Client' present",
                      page.get_by_role("button", name=re.compile(r"invite client", re.I)).count() >= 1)
                check("client_plane: NO raw 'user id' control", "user id" not in body.lower())
                check("client_plane: screenshot", True, "", shot(page, "client_access"))

                # --- the invite flow -------------------------------------------------
                page.get_by_role("button", name=re.compile(r"invite client", re.I)).first.click()
                page.wait_for_timeout(600)
                email_field = page.get_by_label("Client email address")
                check("invite: email field present (no user id)", email_field.count() == 1)
                check("invite: access level selector present",
                      page.get_by_label("Client access level").count() == 1)

                email_field.fill(QA_EMAIL)
                page.get_by_label("Client access level").select_option("member")
                check("invite: form screenshot", True, "", shot(page, "invite_form"))
                page.get_by_role("button", name="Send Invitation").click()
                page.wait_for_timeout(3500)

                sent_body = page.locator("body").inner_text()
                check("invite: NO permission-denied error",
                      "permission" not in sent_body.lower())
                check("invite: QA invitation appears under Pending Invitations",
                      QA_EMAIL in sent_body)
                check("invite: NO token / accept link exposed",
                      "token" not in sent_body.lower()
                      and "accept_url" not in sent_body.lower()
                      and "accept link" not in sent_body.lower())
                check("invite: NO 'Copy link' control",
                      page.get_by_role("button", name=re.compile(r"copy link", re.I)).count() == 0)
                check("invite: sent-state screenshot", True, "", shot(page, "invitation_sent"))

                # --- cleanup: revoke the QA invitation we just created --------------
                row = page.locator("tr", has_text=QA_EMAIL).first
                if row.count() > 0:
                    row.get_by_role("button", name="Revoke").first.click()
                    page.wait_for_timeout(2500)
                    after = page.locator("body").inner_text()
                    check("cleanup: QA invitation revoked",
                          QA_EMAIL not in after or "revoked" in after.lower())
                else:
                    check("cleanup: QA invitation row found for revoke", False, QA_EMAIL)
        except Exception as exc:  # noqa: BLE001
            check("consultant: browser flow", False, str(exc)[:300])
        finally:
            app_errors = [e for e in errors if REALTIME_NOISE not in e]
            notes.append("console errors (verbatim, consultant session): "
                         + (" | ".join(e.split("?")[0] for e in app_errors) or "none"))
            context.close()

        # --- direct customer regression: unchanged members surface ---------------
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            login(page, CUSTOMER_EMAIL, password)
            page.goto(f"{FRONTEND}/organization?tab=members", wait_until="domcontentloaded")
            page.wait_for_timeout(3500)
            check("direct_customer: 'Members & Invitations' kept",
                  page.get_by_role("button", name="Members & Invitations").count() == 1)
            check("direct_customer: NO consultant 'Client Access' surface",
                  page.get_by_role("button", name="Client Access").count() == 0)
            check("direct_customer: screenshot", True, "", shot(page, "direct_customer_members"))
        except Exception as exc:  # noqa: BLE001
            check("direct_customer: browser flow", False, str(exc)[:300])
        finally:
            context.close()

        browser.close()

    failed = [c for c in checks if not c["ok"]]
    return {"checks": checks, "passed": len(checks) - len(failed),
            "failed": len(failed), "ok": not failed, "notes": notes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for item in result["checks"]:
            mark = "PASS" if item["ok"] else "FAIL"
            print(f"[{mark}] {item['check']}"
                  + ("" if item["ok"] else f" :: {item['detail']}"))
        for note in result.get("notes", []):
            print(f"[NOTE] {note}")
        print(f"--- {result['passed']} passed, {result['failed']} failed ---")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


