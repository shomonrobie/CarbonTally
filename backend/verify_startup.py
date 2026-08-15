#!/usr/bin/env python3
"""
CarbonTally V3 - Render startup readiness verification.

Reproduces the exact FastAPI import chain Render runs (``uvicorn main:app``)
and verifies the deployment fixes implemented in this change set:

  A1  routes/admin/staff.py imports ``Client`` from supabase (Render NameError fix)
  B1  routes/admin/workload.py registers BOTH the queue/staff routes (block 1)
      and the appended forecast routes (block 2) - no more router shadowing
  B3  requirements.txt declares PyJWT
  B4  requirements.txt declares reportlab and no longer pins conflicting fpdf==1.7.2
  C1  AuthUser.is_admin exists and is derived from the system-admin role
  C2  organizations/members.py uses Depends(require_auth()) - not Depends(require_auth)
  C1  routes/upload.py batch-access checks use current_user.user_id (no current_user.id)

Run from the ``backend/`` directory with the backend requirements installed:

    cd backend
    python -m pip install -r requirements.txt
    python verify_startup.py

Static source checks run without third-party packages; the full ``import main``
and route-inventory checks require the backend dependencies (Python 3.11.x is
recommended; the pinned pandas==2.1.4 / numpy==1.26.4 need Python <= 3.12).

Exit code 0 -> application imports and every audited fix is present.
Exit code 1 -> at least one check failed (details printed).
"""
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

RESULTS = []  # (name, ok, detail)


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f"  -- {detail}" if detail else ""))


def read(rel_path):
    with open(os.path.join(BACKEND_DIR, rel_path), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Static source checks (do not require third-party packages)
# ---------------------------------------------------------------------------
staff_src = read(os.path.join("routes", "admin", "staff.py"))
check(
    "A1 staff.py imports Client from supabase",
    "from supabase import create_client, Client" in staff_src,
    "expected at staff.py line ~11",
)

workload_src = read(os.path.join("routes", "admin", "workload.py"))
check(
    "B1 workload.py merges forecast router into main router",
    "workload_forecast_router" in workload_src
    and "router.include_router(workload_forecast_router)" in workload_src
    and "@workload_forecast_router.get" in workload_src,
)

req = read("requirements.txt")
check("B3 PyJWT declared in requirements.txt", "PyJWT" in req)
check("B4 reportlab declared in requirements.txt", "reportlab" in req)
check("B4 conflicting fpdf==1.7.2 removed", "fpdf==1.7.2" not in req)

members_src = read(os.path.join("routes", "organizations", "members.py"))
check(
    "C2 members.py uses Depends(require_auth())",
    "Depends(require_auth())" in members_src
    and "Depends(require_auth)" not in members_src.replace("Depends(require_auth())", ""),
    "no bare Depends(require_auth) should remain",
)

upload_src = read(os.path.join("routes", "upload.py"))
check(
    "C1 upload.py batch checks use current_user.user_id",
    "current_user.id" not in upload_src,
    "no current_user.id should remain in upload.py",
)

auth_src = read("auth.py")
check(
    "C1 AuthUser.is_admin populated by get_current_user()",
    "is_admin: bool = False" in auth_src
    and "is_admin=(role == 'admin' or role_name == 'admin')" in auth_src,
)

# ---------------------------------------------------------------------------
# Runtime import + behaviour checks (require the backend dependencies)
# ---------------------------------------------------------------------------
try:
    import main  # noqa: E402
    check("main.py imports (Render startup chain)", True, "main.app created")
except Exception as exc:  # pragma: no cover - surfaced for diagnostics
    check("main.py imports (Render startup chain)", False, f"{type(exc).__name__}: {exc}")
    main = None

if main is not None:
    # C1: AuthUser.is_admin exists (no AttributeError), defaulting to False;
    # the value is derived in get_current_user() (verified by the static check above).
    try:
        from auth import AuthUser

        user = AuthUser(user_id="a", email="a@b.c", role="admin", role_name="admin")
        check("C1 AuthUser.is_admin attribute exists (default False)", user.is_admin is False,
              "populated by get_current_user() from role")
    except Exception as exc:  # pragma: no cover
        check("C1 AuthUser.is_admin attribute exists (default False)", False, f"{type(exc).__name__}: {exc}")

    # B1: both route sets are registered on the workload router
    try:
        from routes.admin import workload

        registered_paths = {
            getattr(route, "path", None) for route in workload.router.routes
        }
        expected_paths = {
            "/api/admin/staff/workload",
            "/api/admin/staff/workload/{staff_id}",
            "/api/admin/queue/settings",
            "/api/admin/queue/stats",
            "/api/admin/queue/reassign",
            "/api/admin/workload/forecast",
            "/api/admin/workload/forecast/summary",
            "/api/admin/workload/forecast/export",
            "/api/admin/workload/forecast/scenarios",
        }
        missing = sorted(expected_paths - registered_paths)
        check(
            "B1 workload router registers queue + forecast routes",
            not missing,
            f"missing: {missing if missing else 'none'}",
        )
    except Exception as exc:  # pragma: no cover
        check(
            "B1 workload router registers queue + forecast routes",
            False,
            f"{type(exc).__name__}: {exc}",
        )

    # A1: staff module imports and its router carries routes
    try:
        from routes.admin import staff

        check("A1 staff router imports and has routes", len(staff.router.routes) > 0,
              f"{len(staff.router.routes)} routes")
    except Exception as exc:  # pragma: no cover
        check("A1 staff router imports and has routes", False, f"{type(exc).__name__}: {exc}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
failed = [item for item in RESULTS if not item[1]]
print()
if failed:
    print(f"RESULT: {len(failed)} of {len(RESULTS)} checks FAILED")
    for name, _, detail in failed:
        print(f"  - FAIL {name}: {detail}")
    sys.exit(1)

print(f"RESULT: all {len(RESULTS)} checks passed")
print("Next steps (run from the backend/ directory):")
print("  uvicorn main:app --host 0.0.0.0 --port 8000")
print("  curl http://127.0.0.1:8000/health")
sys.exit(0)

