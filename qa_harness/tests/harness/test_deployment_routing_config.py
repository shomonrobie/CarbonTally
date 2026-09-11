"""Harness self-tests: production SPA deep-link routing configuration.

Locks the invariant behind the 2026-09-11 production defect in which every deep
link (`/login`, `/privacy`, `/terms`, `/auth/callback`, …) returned Vercel
`404: NOT_FOUND` on a cold load or browser refresh, while client-side navigation
from the home page worked normally.

Root cause (verified against the live deployment, read-only):

* The Vercel CLI project link (`.vercel/project.json`) points the deployment at
  the repository root, so the root `vercel.json` is the effective configuration
  (the build script publishes `frontend/build/*` to the output root `public/`,
  which is why `/` and `/admin` resolve).
* With ``cleanUrls: true``, Vercel removes the extension from every HTML file's
  route ("all HTML files … will have their extension removed"; a request to a
  path ending in the extension receives a 308 to the extensionless path).
  Observed live: `/index.html` -> 308 `/`, `/admin/index.html` -> 308 `/admin`,
  `/zzz.html` -> 308 `/zzz`.
* Because the HTML shell is therefore exposed at `/` (not `/index.html`), every
  SPA rewrite whose destination was an ``…/index.html`` path stopped resolving
  and fell through to a hard 404 - including the trivially correct
  `/admin/(.*)` -> `/admin/index.html` rule (observed: `/admin/deep-path` -> 404).
* `/` itself kept working only because the file-system layer is evaluated before
  the rewrites layer, so the shell is served for the root path regardless.

The fix keeps ``cleanUrls`` explicitly disabled with the canonical
``…/index.html`` rewrite destinations - also the pattern already used by this
repository's other Vercel config (`frontend/vercel.json` and the pre-V3
`frontend_backup_pre_v3_public_20260827/vercel.json`).

These tests are read-only, contact nothing outside the repository, and are
marked ``harness`` (no CarbonTally contact).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_VERCEL_JSON = REPO_ROOT / "vercel.json"
FRONTEND_VERCEL_JSON = REPO_ROOT / "frontend" / "vercel.json"
ROOT_PACKAGE_JSON = REPO_ROOT / "package.json"
FRONTEND_PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"
FRONTEND_SHELL_TEMPLATE = REPO_ROOT / "frontend" / "public" / "index.html"

CATCH_ALL_SOURCE = "/(.*)"


def _load_json(path: Path) -> dict:
    assert path.exists(), f"missing deployment configuration file: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _rewrites(config: dict) -> list[dict]:
    rewrites = config.get("rewrites", [])
    assert isinstance(rewrites, list) and rewrites, "vercel.json must define `rewrites`"
    return rewrites


@pytest.mark.harness
def test_root_vercel_json_is_the_deployment_configuration() -> None:
    """The Vercel project is linked at the repository root and must stay there."""
    link = REPO_ROOT / ".vercel" / "project.json"
    assert link.exists(), (
        ".vercel/project.json is missing - the deployment link target can no longer be "
        "verified, so the effective vercel.json cannot be attributed"
    )
    config = _load_json(ROOT_VERCEL_JSON)
    assert "rewrites" in config


@pytest.mark.harness
def test_clean_urls_must_stay_disabled_while_rewrites_target_index_html() -> None:
    """`cleanUrls: true` removes the extension from HTML routes, which breaks SPA rewrites.

    Reintroducing ``cleanUrls: true`` while any rewrite destination ends in
    ``.html`` silently turns every deep link (and the OAuth callback) into a 404.
    """
    config = _load_json(ROOT_VERCEL_JSON)
    html_destinations = sorted(
        r.get("destination", "") for r in _rewrites(config) if r.get("destination", "").endswith(".html")
    )
    assert html_destinations, (
        "the SPA shell rewrite destinations are no longer `*.html`; re-verify the cleanUrls "
        "invariant before changing this test"
    )
    assert config.get("cleanUrls") is False, (
        "vercel.json must set `cleanUrls` explicitly to false: the SPA rewrites target "
        f"{html_destinations}, and cleanUrls removes the .html extension from HTML routes, "
        "leaving those destinations unresolvable (production deep links then 404 on refresh)"
    )


@pytest.mark.harness
def test_spa_catch_all_is_present_and_last() -> None:
    """Unmatched paths must resolve to the application shell, never to a bare 404."""
    rewrites = _rewrites(_load_json(ROOT_VERCEL_JSON))
    catch_all = [r for r in rewrites if r.get("source") == CATCH_ALL_SOURCE]
    assert len(catch_all) == 1, f"exactly one {CATCH_ALL_SOURCE!r} catch-all rewrite is required"
    assert catch_all[0]["destination"] == "/index.html", (
        "the catch-all must target /index.html - the shell path actually produced by the "
        "root build script (`cp -r frontend/build/* public/`)"
    )
    assert rewrites[-1] is catch_all[0], "the catch-all rewrite must be the last rule so it never shadows a real asset"


@pytest.mark.harness
def test_asset_shields_precede_the_catch_all() -> None:
    """Static-asset rules must be evaluated before the shell rewrite."""
    rewrites = _rewrites(_load_json(ROOT_VERCEL_JSON))
    catch_all_index = next(i for i, r in enumerate(rewrites) if r.get("source") == CATCH_ALL_SOURCE)
    for pattern in (r"^/static/", r"^/admin/static/", r"^/admin/"):
        shield_indexes = [i for i, r in enumerate(rewrites) if re.match(pattern, r.get("source", ""))]
        assert shield_indexes, f"missing rewrite shield for {pattern}"
        assert max(shield_indexes) < catch_all_index, f"shield {pattern} must precede the catch-all rewrite"


@pytest.mark.harness
def test_secondary_vercel_config_does_not_reenable_clean_urls() -> None:
    """`frontend/vercel.json` is inert while the link target is the repository root.

    It must nevertheless stay consistent: if the Vercel Root Directory were ever
    switched to `frontend/`, this file becomes the effective configuration.
    """
    if not FRONTEND_VERCEL_JSON.exists():
        pytest.skip("frontend/vercel.json not present")
    config = _load_json(FRONTEND_VERCEL_JSON)
    assert config.get("cleanUrls") is not True, (
        "frontend/vercel.json must not enable cleanUrls - it would break its own "
        "catch-all rewrite to /index.html if that config ever became effective"
    )


@pytest.mark.harness
def test_deep_links_load_assets_from_absolute_paths() -> None:
    """A shell served at /login must still load /static/... assets."""
    frontend_package = _load_json(FRONTEND_PACKAGE_JSON)
    assert frontend_package.get("homepage") == "/", (
        "frontend/package.json `homepage` must stay '/' so the built shell references assets "
        "absolutely; a relative homepage breaks asset loading for nested deep links"
    )
    template = FRONTEND_SHELL_TEMPLATE.read_text(encoding="utf-8")
    assert "%PUBLIC_URL%" in template, "the shell template must use %PUBLIC_URL% for asset and icon URLs"


@pytest.mark.harness
def test_build_publishes_the_shell_to_the_output_root() -> None:
    """The `/index.html` rewrite destination must be produced by the production build."""
    build_script = _load_json(ROOT_PACKAGE_JSON)["scripts"]["build"]
    assert "frontend/build" in build_script and "public/" in build_script, (
        "the root build script must publish frontend/build into the deployment output "
        f"directory; found: {build_script!r}"
    )
