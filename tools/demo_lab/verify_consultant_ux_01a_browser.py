#!/usr/bin/env python3
"""CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A — BROWSER verification.

Drives the REAL frontend at http://localhost:3000 with real headless Chrome and a
REAL password login against the lab GoTrue (no token injection). It proves the
human-UX contract this follow-up task establishes:

* the Consultant Plane has NO global "Active client" selector (UX-01/AC-01);
* Clients is the human entry point ("Open workspace") (AC-03/AC-04);
* the Client Operating Plane has EXACTLY ONE "Back to Consultant" and NO
  "Switch client" (AC-05/AC-06/AC-07);
* firm pages (branding / white-label / team / manual-processing) carry no client
  context (AC-09..AC-12);
* Team adds a member by EMAIL, never by internal user id (AC-14/AC-15);
* a Firm Task links a client by a human-readable selector (AC-17/AC-18);
* a DIRECT customer sees none of the consultant context (AC-20).

Reads only; writes only screenshots into the lab evidence directory.

Usage::

    ~/ct_local_env/pwvenv/bin/python tools/demo_lab/verify_consultant_ux_01a_browser.py
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

FRONTEND = "http://localhost:3000"
CHROME = "/usr/bin/google-chrome"
REALTIME_NOISE = "realtime/v1/websocket"
CONSULTANT_EMAIL = "consultant.owner@demo-lab.carbontally.local"
CUSTOMER_EMAIL = "owner.clienta@demo-lab.carbontally.local"
FIRM_NAME = "Demo Lab Carbon Consultants"


def shot(page, name: str) -> str:
    lab.ensure_dirs()
    out = lab.EVIDENCE_DIR / "browser" / f"ct_ux01a_{name}.png"
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


def _has_active_client_label(body: str) -> bool:
    # The old global selector rendered the exact line "Active client". "Active
    # clients" (the dashboard summary card, plural) is a different string.
    return re.search(r"(?m)^Active client$", body) is not None


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
            page.goto(f"{FRONTEND}/consultant", wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.body && document.body.innerText.includes('multi-client portal')",
                timeout=30000)
            page.wait_for_timeout(1200)
            body = page.locator("body").inner_text()

            # --- Consultant dashboard: firm plane, NO active client -----------------
            check("consultant_plane: firm identity shown", FIRM_NAME in body)
            check("consultant_plane: NO 'Active client' label",
                  not _has_active_client_label(body))
            check("consultant_plane: NO 'Select active client' selector",
                  page.get_by_label("Select active client").count() == 0)
            check("consultant_plane: NO legacy client switcher element",
                  page.locator(".v3-client-switcher").count() == 0)
            check("consultant_plane: dashboard screenshot", True, "", shot(page, "dashboard"))

            # --- Clients directory: human entry point ------------------------------
            page.get_by_role("button", name="Clients", exact=True).click()
            page.wait_for_timeout(1200)
            clients_body = page.locator("body").inner_text()
            check("clients: directory shows 'Open workspace'", "Open workspace" in clients_body)
            check("clients: still NO 'Active client' label",
                  not _has_active_client_label(clients_body))
            check("clients: screenshot", True, "", shot(page, "clients"))

            # --- Client Operating Plane --------------------------------------------
            open_btn = page.get_by_role("button", name="Open workspace").first
            if open_btn.count() == 0:
                check("client_plane: a managed client exists to open", False,
                      "no Open workspace action on the Clients tab")
            else:
                open_btn.click()
                page.wait_for_timeout(3500)
                m = re.search(r"/consultant/clients/([^/]+)/", page.url)
                client_id = m.group(1) if m else None
                check("client_plane: opened /consultant/clients/:id/*", bool(client_id), page.url)
                plane_body = page.locator("body").inner_text()
                check("client_plane: actor = consultant firm",
                      "Consultant" in plane_body and FIRM_NAME in plane_body)
                check("client_plane: subject = 'Working on' the client",
                      "working on" in plane_body.lower())
                check("client_plane: EXACTLY ONE 'Back to Consultant'",
                      page.get_by_text("Back to Consultant").count() == 1,
                      f"count={page.get_by_text('Back to Consultant').count()}")
                check("client_plane: NO 'Switch client' control",
                      page.get_by_text("Switch client").count() == 0
                      and page.get_by_label("Switch client").count() == 0)
                check("client_plane: NO 'Active client' label",
                      not _has_active_client_label(plane_body))
                check("client_plane: Home subtitle is consultant-operated, not 'customer'",
                      "Consultant-operated client workspace" in plane_body)
                check("client_plane: screenshot", True, "", shot(page, "client_plane"))

                # The single return path works.
                page.get_by_test_id("client-operating-context").get_by_role(
                    "link", name="Back to Consultant").first.click()
                page.wait_for_timeout(1500)
                check("client_plane: 'Back to Consultant' returns to /consultant",
                      page.url.rstrip("/").endswith("/consultant"), page.url)

                # --- Firm-level pages carry NO client context ----------------------
                for label, slug in [
                    ("Firm branding", "branding"),
                    ("White-label", "whitelabel"),
                    ("Team", "team"),
                    ("Manual Processing", "coverage"),
                ]:
                    page.get_by_role("button", name=label, exact=True).click()
                    page.wait_for_timeout(1500)
                    fb = page.locator("body").inner_text()
                    check(f"firm_page[{slug}]: NO 'Active client' label",
                          not _has_active_client_label(fb), slug)
                    check(f"firm_page[{slug}]: NO 'Select active client' selector",
                          page.get_by_label("Select active client").count() == 0, slug)
                    check(f"firm_page[{slug}]: screenshot", True, "", shot(page, slug))
                    if slug == "team":
                        check("team: NO raw 'User id' field", "User id" not in fb)
                        check("team: 'Email' identity field present",
                              page.get_by_label("Email").count() >= 1)
                        role_values = page.eval_on_selector_all(
                            "#team-member-role option", "els => els.map(e => e.value)")
                        check("team: role list is the REAL backend vocabulary",
                              role_values == ["consultant", "manager", "viewer", "owner"],
                              str(role_values))
                        check("team: no invented 'consultant team member' role",
                              "consultant team member" not in role_values)
                        # Add-team-member state (focus the email field).
                        page.get_by_label("Email").first.click()
                        page.get_by_label("Email").first.fill(
                            "new.colleague@demo-lab.carbontally.local")
                        page.wait_for_timeout(400)
                        check("team: add-member state screenshot", True, "",
                              shot(page, "team_add_member"))
                        page.get_by_label("Email").first.fill("")
                        # Firm-task client selector is human-readable.
                        client_opts = page.eval_on_selector_all(
                            "#task-client option", "els => els.map(e => e.textContent)")
                        check("firm_task: client selector present and human-readable",
                              bool(client_opts)
                              and client_opts[0].startswith("— No specific client"),
                              str(client_opts[:3]))
                        # Open the selector for the screenshot.
                        page.click("#task-client")
                        page.wait_for_timeout(400)
                        check("firm_task: client-selector state screenshot", True, "",
                              shot(page, "firm_task_client_select"))

                # --- Client Messages: local client selection -----------------------
                page.get_by_role("button", name="Client messages").click()
                page.wait_for_timeout(1500)
                check("client_messages: local 'Client' selector offered",
                      page.get_by_label("Client").count() >= 1)
                check("client_messages: screenshot", True, "", shot(page, "client_messages"))
        except Exception as exc:  # noqa: BLE001
            check("consultant: browser flow", False, str(exc)[:300])
        finally:
            realtime = [e for e in errors if REALTIME_NOISE in e]
            app_errors = [e for e in errors if REALTIME_NOISE not in e]
            notes.append("console errors (verbatim, consultant session): "
                         + (" | ".join(e.split("?")[0] for e in app_errors) or "none"))
            uncaught = [e for e in app_errors
                        if "Failed to load resource" not in e
                        and "[CarbonTally V3]" not in e]
            check("consultant: no UNCAUGHT application console errors",
                  not uncaught, " | ".join(uncaught)[:300])
            if realtime:
                notes.append(f"{len(realtime)} realtime WebSocket handshake error(s) — "
                             "Demo Lab gateway environment limitation, not a defect")
            context.close()

        # Direct-customer regression: no consultant context leaks onto a customer.
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            login(page, CUSTOMER_EMAIL, password)
            page.goto(f"{FRONTEND}/home", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            body = page.locator("body").inner_text()
            check("direct_customer: home renders customer nav",
                  "Documents" in body and "Processing" in body)
            check("direct_customer: NO 'Back to Consultant' leak",
                  "Back to Consultant" not in body)
            check("direct_customer: NO 'Working on:' consultant context",
                  "Working on:" not in body)
            check("direct_customer: keeps its own 'V3 customer workspace' wording",
                  "V3 customer workspace" in body)
            check("direct_customer: screenshot", True, "", shot(page, "direct_customer_home"))
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



