# CarbonTally V3 - Production OCR (Tesseract/Poppler) Provisioning Handoff

**Status:** APPLICATION CODE COMPLETE - production provisioning requires authorized access to the
Render deployment configuration.
**Date:** 26 August 2026
**Author:** Cline

---

## 1. Deployment discovery (verified, not assumed)

| Item | Value | Evidence |
|---|---|---|
| Hosting provider | **Render** | `docs/audit/cline/CarbonTally_V3_Render_Runtime_Readiness_Audit_v1.0.md`; `backend/config.py` CORS allow-list contains `https://carbontally-api.onrender.com`; `docs/RECONSTRUCTED_TASK_HISTORY.md` "Render deployment prep" commits |
| Service | **`carbontally-api`** (web service) | `https://carbontally-api.onrender.com` (DNS resolves to `216.24.57.x`, Render GCP us-west-1) |
| Runtime | **Render Native Python runtime** (NOT Docker) | Render runtime audit §1: start command `uvicorn main:app`; traceback paths `/opt/render/project/src/backend/...` are the native-runtime layout |
| Build mechanism | `pip install -r backend/requirements.txt` (Render "Python requirements path") | Runtime audit §1/§F |
| Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` run from `backend/`, `RELOAD=false` | Runtime audit §1/§F |
| Python version | `3.11.9` pinned via root `runtime.txt` | git history commit `308c7a5`; `runtime.txt` tracked |
| Requirements file | `backend/requirements.txt` | git history commit `35dbcd6`; runtime audit confirms it is the effective file |
| Configuration location | **Render Dashboard** (Settings -> Build & Deploy). No `render.yaml`/`Dockerfile`/`Procfile`/`.github/workflows` has ever been tracked in git history (verified `git log --all --name-only`) | runtime audit §1; git history |

## 2. Access (verified)

- **Render CLI:** not installed (`which render` -> none).
- **Render API key / `RENDER_API_KEY`:** not set in the environment (existence check only; no secrets inspected or reproduced).
- **`render.yaml` / blueprint:** none in the repository, none anywhere on this machine (`find /home/shomonrobie -iname 'render.y*ml'` -> none).
- **Production endpoint:** `https://carbontally-api.onrender.com/health` -> HTTP 000 from this environment (Render free-tier services sleep; no outbound path established). No production smoke test is possible from here.
- **Authorized access to modify deployment:** **NONE in this environment.**

## 3. Provisioning decision (why not a repo change alone)

Render Native runtimes run on Debian 12 "bookworm" with a preloaded tool set. Render's
documentation explicitly lists the available tools - **`tesseract` and `poppler-utils` are NOT
included** - and states: *"To use a tool that isn't included in Render's native runtimes ... you can
deploy with Docker instead."* Adding system packages via a custom Build Command on the Native
runtime is possible to *attempt* but is not Render's supported path and cannot be verified from
this environment. Changing the deployment to Docker is out of scope for this task (it would
redesign the existing, working dashboard-configured deployment).

Therefore: **application code is complete; the only missing step is a configuration change in the
authorized Render service**, which requires access that is not present here.

## 4. Exact deployment change required

### Option A - Custom Build Command on the existing Native Python runtime (dashboard only)

In the Render Dashboard -> `carbontally-api` -> Settings -> Build & Deploy:

| Setting | Current | Change to |
|---|---|---|
| Python version | 3.11 (from `runtime.txt`) | unchanged |
| Requirements path | `backend/requirements.txt` | unchanged |
| Build Command | *(default)* | `apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng libtesseract5 libleptonica6 poppler-utils && pip install -r backend/requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` (from `backend/`) | unchanged |
| Environment | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RESEND_API_KEY` | unchanged |

> Caveat (must be verified on Render): native-runtime build commands run on the build image;
> whether apt-installed binaries persist to the runtime image is not guaranteed by Render's docs
> for Native runtimes. If the app starts but OCR reports "tesseract not found", switch to Option B.

### Option B - Dockerfile (Render-recommended for non-bundled system tools)

If Option A's build->runtime persistence is not honoured, deploy the backend as a Docker service.
Reference Dockerfile (documented for the authorized operator - **not added to the repo**):

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng libtesseract5 libleptonica6 poppler-utils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> Option B changes the deployment mechanism and should only be applied after a Product Owner
> decision (it is a deployment redesign, out of this task's scope).

## 5. Required environment variables (unchanged)

`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RESEND_API_KEY` - already set on
the Render service. **No new secrets are required.** `TESSERACT_CMD`/`TESSDATA_PREFIX`/
`LD_LIBRARY_PATH` are **not** required on Render if the packages are installed system-wide via apt
(binary at `/usr/bin/tesseract`, trained data at `/usr/share/tesseract-ocr/5/tessdata/eng.traineddata`,
libs in `/usr/lib/x86_64-linux-gnu`). They are only needed for the local no-root provisioning
(`tools/provision_tesseract_local.sh`).

## 6. Exact verification commands (run after the authorized operator applies the change)

On the deployed instance (Render Dashboard -> Shell / one-off job, or a temporary version-reporting
endpoint):

```bash
which tesseract && tesseract --version         # expect: tesseract 5.x, leptonica
which pdftoppm && pdftoppm -v 2>&1 | head -1   # expect: pdftoppm version 22.xx (poppler)
```

Smoke test (synthetic documents only - NEVER real customer documents):

```bash
curl -s https://carbontally-api.onrender.com/health   # expect 200 {"status":"healthy",...}
```

Then, with a demo-owner session token against production, upload
`/tmp/synth_docs/electricity_scanned.pdf` via `POST /api/v3/uploads` and confirm:
1. `organization_files.metadata.ocr.status == "ok"` and `method == "tesseract_ocr"`;
2. the item workspace returns `source.ocr_text` and `source.ocr_suggestions`;
3. `data.extracted_data == {}` and item status `pending` (no automatic approval);
4. `POST /api/v3/uploads/{file_id}/ocr` re-run returns the same `ok` summary.

## 7. What access is required

- Dashboard/owner-level access to the Render service `carbontally-api` (Render workspace
  `shomonrobie`/owner) to edit the Build Command, or
- a `render.yaml` blueprint applied via `render blueprints apply` from an environment with a valid
  `RENDER_API_KEY`, or
- Render API credentials (`RENDER_API_KEY`) + the service ID to update `buildCommand` via the
  `services/{id}` API and trigger a deploy.

## 8. What was NOT changed

- No OCR code, no `render.yaml`, no `Dockerfile`, no `runtime.txt`, no `requirements.txt`, no
  environment variables, no schema, no RLS. The only artifact this handoff adds is this document
  and the report updates.

## 9. Conclusion

**"Application code is complete; production provisioning requires authorized access to the
deployment configuration."** The exact settings, commands, and verification steps are above.
