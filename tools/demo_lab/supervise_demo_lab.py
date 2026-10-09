#!/usr/bin/env python3
"""DEMO-T1 persistence — keep the local Demo Lab continuously available.

The Demo Lab has two layers:

* **containers** — the developer's local Supabase stack plus the three lab
  containers. These are already durable: every one of them is created with
  ``--restart unless-stopped`` (``stack.py`` / ``storage.py``) and the Docker
  daemon is enabled at boot, so they survive a process crash and a reboot with
  no help from this script.
* **release processes** — the release backend (``uvicorn`` on 127.0.0.1:8070) and
  the CRA development frontend (http://localhost:3000). ``run_demo_lab.sh``
  started the backend with a bare ``nohup`` and did not start the frontend at
  all, so neither process came back after a crash and neither survived the
  terminal that launched it.

This script is the smallest local mechanism that closes that second gap. It is
stdlib-only, adds no dependency, writes nothing outside the existing Demo Lab
state directory, and never touches production, Render, hosted Supabase, the
investor demo dataset, RLS, migrations or application code.

Usage::

    python3 tools/demo_lab/supervise_demo_lab.py start      # ensure stack + start supervised
    python3 tools/demo_lab/supervise_demo_lab.py status     # health report (exit 1 unless healthy)
    python3 tools/demo_lab/supervise_demo_lab.py restart
    python3 tools/demo_lab/supervise_demo_lab.py stop
    python3 tools/demo_lab/supervise_demo_lab.py logs [backend|frontend]

``start`` spawns a detached supervisor (new session, no controlling terminal),
so closing the terminal/IDE does not stop the Demo Lab. The supervisor restarts
either release process after an ordinary failure.

Machine reboot: the containers return by themselves (Docker restart policy). The
release processes are brought back by the ``systemd --user`` unit shipped at
``tools/demo_lab/systemd/carbontally-demo-lab.service`` (``run
--ensure-containers``), which is installed at ``~/.config/systemd/user/`` and
enabled — with ``loginctl enable-linger`` so it starts at BOOT, not merely at
login. See ``README.md`` §9.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import lab  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

#: DR-003: the only browser origin the lab accepts is http://localhost:3000
#: (stack.py BROWSER_ORIGIN == GoTrue GOTRUE_SITE_URL == backend ALLOWED_ORIGINS).
FRONTEND_ORIGIN = "http://localhost:3000"
FRONTEND_PORT = 3000
BACKEND_ORIGIN = f"http://127.0.0.1:{lab.BACKEND_PORT}"
GATEWAY_ORIGIN = f"http://127.0.0.1:{lab.GATEWAY_PORT}"

ENV_PATH = lab.STATE_DIR / "backend.env"
PID_PATH = lab.STATE_DIR / "supervisor.pid"
STATUS_PATH = lab.STATE_DIR / "supervisor.status.json"
LOG_DIR = lab.STATE_DIR / "logs"
SUPERVISOR_LOG = LOG_DIR / "supervisor.log"

#: Containers without which the Demo Lab cannot serve the application. A missing
#: one is fatal here (rebuild with run_demo_lab.sh); a stopped one is started.
REQUIRED_CONTAINERS = (
    lab.STACK_DB_CONTAINER,
    lab.STACK_AUTH_CONTAINER,
    lab.STACK_STORAGE_CONTAINER,
    lab.POSTGREST_CONTAINER,
    lab.STORAGE_CONTAINER,
    lab.GATEWAY_CONTAINER,
)
#: The rest of the local Supabase stack: started when stopped, absence tolerated.
OPTIONAL_CONTAINERS = tuple(
    name for name in (
        "supabase_kong_carbon_ledger",
        "supabase_rest_carbon_ledger",
        "supabase_pg_meta_carbon_ledger",
        "supabase_realtime_carbon_ledger",
        "supabase_inbucket_carbon_ledger",
        "supabase_studio_carbon_ledger",
    ) if name not in REQUIRED_CONTAINERS
)

POLL_SECONDS = 2.0
RESTART_DELAY = 2.0
MAX_RESTART_DELAY = 30.0
#: A child that stays up longer than this counts as healthy, so its next crash
#: restarts with the base delay instead of a growing backoff.
HEALTHY_UPTIME = 30.0

# --- logging / state -------------------------------------------------------


def log(message: str) -> None:
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {message}"
    print(line, flush=True)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with SUPERVISOR_LOG.open("a") as handle:
            handle.write(line + "\n")
    except OSError:  # logging must never be the reason the lab is unavailable
        pass


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def read_pid() -> int | None:
    try:
        return int(PID_PATH.read_text().strip())
    except (OSError, ValueError):
        return None


def write_status(payload: dict) -> None:
    try:
        lab.ensure_dirs()
        STATUS_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except OSError:
        pass


# --- local process discovery (conservative: Demo Lab processes only) --------

BACKEND_MARKERS = ("uvicorn", "main:app", f"--port {lab.BACKEND_PORT}")


def _cmdline(pid: int) -> str:
    try:
        raw = pathlib.Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\x00", b" ").decode("utf-8", "replace").strip()


def _cwd(pid: int) -> str:
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return ""


def demo_lab_processes() -> list[tuple[int, str]]:
    """Processes recognisably this Demo Lab's release backend/frontend.

    Deliberately strict: a process is reported only when its command line
    carries the lab's own port/markers or its working directory is this
    repository's ``frontend/``. Unrelated processes are never matched.
    """
    found: list[tuple[int, str]] = []
    own = {os.getpid(), os.getppid()}
    for entry in pathlib.Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid in own:
            continue
        cmdline = _cmdline(pid)
        if not cmdline or "supervise_demo_lab.py" in cmdline:
            continue
        is_backend = all(marker in cmdline for marker in BACKEND_MARKERS)
        is_frontend = (
            "react-scripts" in cmdline
            and " start" in f" {cmdline}"
            and _cwd(pid).rstrip("/") == str(FRONTEND_DIR)
        )
        if is_backend or is_frontend:
            found.append((pid, cmdline))
    return found


def _terminate(pid: int, *, grace: float = 10.0) -> None:
    """TERM the process group, then KILL it if it is still there."""
    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except OSError:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            return
    deadline = time.time() + grace
    while time.time() < deadline:
        if not process_alive(pid):
            return
        time.sleep(0.2)
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except OSError:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass


def stop_unsupervised_lab_processes() -> list[str]:
    """Stop leftover backend/frontend processes this supervisor did not start."""
    stopped = []
    for pid, cmdline in demo_lab_processes():
        _terminate(pid)
        stopped.append(f"{pid}:{cmdline[:90]}")
    return stopped


# --- lab gateway upstream repair -------------------------------------------

#: (gateway path, upstream container, upstream port, upstream path). The lab
#: gateway resolves these names at nginx start-up (stack.py:233-236). When a
#: Supabase container is later recreated it gets a new IP, the Docker restart
#: policy keeps everything "running", and the gateway silently returns 502 for
#: that route (observed live: nginx still pointing at 172.21.0.8 while the auth
#: container had moved to 172.21.0.10). Restarting the gateway re-resolves.
GATEWAY_ROUTES = (
    ("/auth/v1/health", lab.STACK_AUTH_CONTAINER, 9999, "/health"),
    ("/rest/v1/", lab.POSTGREST_CONTAINER, 3000, "/"),
    ("/storage/v1/version", lab.STORAGE_CONTAINER, 5000, "/version"),
)
GATEWAY_REPAIR_INTERVAL = 60.0


def _gateway_route_ok(path: str) -> bool:
    status, _headers, _body = http_probe(f"{GATEWAY_ORIGIN}{path}", timeout=5.0)
    return status not in (0, 502, 504)


def _gateway_upstream_ok(container: str, port: int, path: str) -> bool:
    """Can the gateway reach the upstream directly (DNS + TCP + HTTP)?"""
    probe = lab.run(["docker", "exec", lab.GATEWAY_CONTAINER, "wget", "-q", "-O", "-",
                     "--timeout=5", f"http://{container}:{port}{path}"], timeout=60)
    return probe.returncode == 0


def ensure_gateway_upstreams() -> dict:
    """Repair the gateway when nginx holds a stale upstream IP.

    Read-only until something is actually broken: a route that answers is left
    alone. Only the disposable lab gateway container is ever restarted.
    """
    report = {"unreachable": [], "repaired": False, "still_unreachable": []}
    for path, container, port, upstream_path in GATEWAY_ROUTES:
        if _gateway_route_ok(path):
            continue
        direct = _gateway_upstream_ok(container, port, upstream_path)
        report["unreachable"].append(
            f"{path} (upstream {container}:{port} "
            f"direct={'ok' if direct else 'unreachable'})")
    if not report["unreachable"]:
        return report
    log("gateway: unreachable route(s) — restarting the lab gateway to "
        "re-resolve upstreams: " + "; ".join(report["unreachable"]))
    lab.run(["docker", "restart", lab.GATEWAY_CONTAINER], timeout=120)
    for _ in range(20):
        if _gateway_route_ok("/auth/v1/health"):
            break
        time.sleep(1.5)
    report["repaired"] = all(_gateway_route_ok(path) for path, *_ in GATEWAY_ROUTES)
    if report["repaired"]:
        log("gateway: upstreams reachable again")
    else:
        report["still_unreachable"] = [
            path for path, *_ in GATEWAY_ROUTES if not _gateway_route_ok(path)]
        log("gateway: still unreachable after restart: "
            + ", ".join(report["still_unreachable"]))
    return report


# --- health probes ---------------------------------------------------------



def http_probe(url: str, *, method: str = "GET", headers: dict | None = None,
               timeout: float = 6.0):
    """Return ``(status, headers, body)``; status 0 means unreachable."""
    request = urllib.request.Request(url, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, dict(response.headers), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        return exc.code, dict(exc.headers), body
    except Exception as exc:  # noqa: BLE001 — a probe failure is data, not an error
        return 0, {}, str(exc)


def probe_database() -> dict:
    try:
        return {"ok": lab.psql_scalar("SELECT 1") == "1",
                "detail": f"{lab.LAB_DB} on 127.0.0.1:{lab.STACK_DB_PORT}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(exc).__name__}: {exc}"[:200]}


def probe_gateway() -> dict:
    status, _headers, body = http_probe(f"{GATEWAY_ORIGIN}/auth/v1/health")
    return {"ok": status == 200, "detail": f"GET /auth/v1/health -> {status}",
            "body": body[:120]}


def probe_backend() -> dict:
    status, _headers, body = http_probe(f"{BACKEND_ORIGIN}/health")
    return {"ok": status == 200, "detail": f"GET /health -> {status}", "body": body[:120]}


def probe_frontend() -> dict:
    status, _headers, body = http_probe(f"{FRONTEND_ORIGIN}/")
    served = status == 200 and 'id="root"' in body
    return {"ok": served, "detail": f"GET / -> {status} (app shell served: {served})"}


def probe_browser_cors() -> dict:
    """Simulate the browser's preflight: frontend origin -> release backend."""
    status, headers, _body = http_probe(
        f"{BACKEND_ORIGIN}/api/v3/me/context", method="OPTIONS",
        headers={"Origin": FRONTEND_ORIGIN,
                 "Access-Control-Request-Method": "GET"})
    allowed = headers.get("access-control-allow-origin", "")
    return {"ok": allowed == FRONTEND_ORIGIN,
            "detail": f"OPTIONS /api/v3/me/context -> {status}, "
                      f"allow-origin={allowed or '<none>'}"}


def health_report() -> dict:
    supervisor_pid = read_pid()
    supervised = bool(supervisor_pid and process_alive(supervisor_pid))
    payload = {
        "supervisor": {"pid": supervisor_pid, "running": supervised},
        "containers": {name: lab.container_state(name)
                       for name in REQUIRED_CONTAINERS + OPTIONAL_CONTAINERS},
        "probes": {
            "database": probe_database(),
            "gateway": probe_gateway(),
            "backend": probe_backend(),
            "frontend": probe_frontend(),
            "frontend_to_backend_cors": probe_browser_cors(),
        },
        "urls": {"frontend": FRONTEND_ORIGIN, "backend": BACKEND_ORIGIN,
                 "gateway": GATEWAY_ORIGIN},
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if STATUS_PATH.exists():
        try:
            recorded = json.loads(STATUS_PATH.read_text())
            payload["supervisor"]["components"] = recorded.get("components", {})
            payload["supervisor"]["state"] = recorded.get("state")
        except (OSError, json.JSONDecodeError):
            pass
    payload["healthy"] = bool(
        supervised
        and payload["probes"]["database"]["ok"]
        and payload["probes"]["gateway"]["ok"]
        and payload["probes"]["backend"]["ok"]
        and payload["probes"]["frontend"]["ok"]
    )
    return payload


def print_status(payload: dict) -> None:
    containers = payload["containers"]
    supervisor = payload["supervisor"]
    print(f"DEMO_LAB_STATUS: {'RUNNING' if payload['healthy'] else 'BLOCKED'}")
    print(f"supervisor     : pid={supervisor.get('pid')} "
          f"running={supervisor.get('running')} state={supervisor.get('state')}")
    for name in REQUIRED_CONTAINERS + OPTIONAL_CONTAINERS:
        required = " (required)" if name in REQUIRED_CONTAINERS else ""
        print(f"  container    : {name} -> {containers.get(name)}{required}")
    for name, probe in payload["probes"].items():
        print(f"  probe {name:<24}: {'PASS' if probe['ok'] else 'FAIL'} — {probe['detail']}")
    for name, component in (supervisor.get("components") or {}).items():
        print(f"  supervised {name:<12}: pid={component.get('pid')} "
              f"restarts={component.get('restarts')} "
              f"last_exit_code={component.get('last_exit_code')}")
    print(f"frontend: {payload['urls']['frontend']}")
    print(f"backend : {payload['urls']['backend']}")
    print(f"gateway : {payload['urls']['gateway']}")


# --- container start -------------------------------------------------------


def ensure_containers() -> dict:
    """Start any stopped required/optional container. Fail closed on absence."""
    result: dict[str, list[str]] = {"started": [], "already": [], "absent": [],
                                    "failed": []}
    for name in REQUIRED_CONTAINERS + OPTIONAL_CONTAINERS:
        state = lab.container_state(name)
        if state == "running":
            result["already"].append(name)
            continue
        if state == "absent":
            result["absent"].append(name)
            continue
        started = lab.run(["docker", "start", name], timeout=120)
        if started.returncode == 0:
            result["started"].append(name)
            log(f"containers: started stopped container {name}")
        else:
            result["failed"].append(name)
            log(f"containers: could not start {name}: {started.stderr.strip()[:200]}")
    missing_required = [n for n in REQUIRED_CONTAINERS if n in result["absent"]]
    if missing_required:
        raise RuntimeError(
            "Demo Lab containers are missing: " + ", ".join(missing_required)
            + "\nBuild/repair the Demo Lab first: ./tools/demo_lab/run_demo_lab.sh")
    return result


# --- supervised release processes ------------------------------------------


class Component:
    """One supervised release process (backend or frontend)."""

    def __init__(self, name: str, argv: list[str], cwd: pathlib.Path, env: dict,
                 url: str) -> None:
        self.name = name
        self.argv = argv
        self.cwd = cwd
        self.env = env
        self.url = url
        self.log_path = LOG_DIR / f"{name}.log"
        self.proc: subprocess.Popen | None = None
        self.restarts = 0
        self.started_at: float | None = None
        self.last_exit_code: int | None = None
        self.crash_loop = 0

    def start(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a") as handle:
            handle.write(
                f"\n=== {time.strftime('%Y-%m-%dT%H:%M:%S%z')} supervisor starting "
                f"{self.name}: {' '.join(self.argv)}\n")
            handle.flush()
            self.proc = subprocess.Popen(
                self.argv, cwd=str(self.cwd), env=self.env,
                stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT,
                start_new_session=True)
        self.started_at = time.time()
        self.last_exit_code = None
        log(f"{self.name}: started pid={self.proc.pid}")

    def stop(self, *, grace: float = 15.0) -> None:
        if not self.proc or self.proc.poll() is not None:
            return
        _terminate(self.proc.pid, grace=grace)
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        log(f"{self.name}: stopped")

    def restart_delay(self) -> float:
        """Base delay, backing off only while the process keeps dying young."""
        if self.started_at and (time.time() - self.started_at) > HEALTHY_UPTIME:
            self.crash_loop = 0
        delay = min(RESTART_DELAY * (2 ** self.crash_loop), MAX_RESTART_DELAY)
        self.crash_loop = min(self.crash_loop + 1, 5)
        return delay

    def status(self) -> dict:
        return {
            "pid": self.proc.pid if self.proc else None,
            "running": bool(self.proc and self.proc.poll() is None),
            "restarts": self.restarts,
            "last_exit_code": self.last_exit_code,
            "url": self.url,
            "log": str(self.log_path),
        }


def parse_env_file(path: pathlib.Path) -> dict:
    """Minimal ``KEY=VALUE`` reader (the lab env file is machine-generated)."""
    env: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"')
    return env


def build_components(*, with_backend: bool, with_frontend: bool) -> list[Component]:
    components: list[Component] = []
    if with_backend:
        if not ENV_PATH.exists():
            raise RuntimeError(
                f"missing lab backend environment: {ENV_PATH}\n"
                "Generate it first: python3 tools/demo_lab/lab_env.py --write")
        uvicorn = BACKEND_DIR / ".venv" / "bin" / "uvicorn"
        if not uvicorn.exists():
            raise RuntimeError(f"missing backend virtualenv: {uvicorn}")
        env = {**os.environ, **parse_env_file(ENV_PATH)}
        components.append(Component(
            "backend",
            [str(uvicorn), "main:app", "--host", "127.0.0.1",
             "--port", str(lab.BACKEND_PORT)],
            BACKEND_DIR, env, f"{BACKEND_ORIGIN}/health"))
    if with_frontend:
        react_scripts = FRONTEND_DIR / "node_modules" / ".bin" / "react-scripts"
        if not react_scripts.exists():
            raise RuntimeError(
                f"missing frontend dependencies: {react_scripts}\n"
                f"Install them first: cd {FRONTEND_DIR} && npm install")
        # dotenv never overwrites an already-set variable, so these win over
        # frontend/.env.local. PORT must be 3000 (DR-003: the lab accepts only
        # http://localhost:3000 — :3100 is rejected by CORS and the browser then
        # reports a failed login).
        env = {**os.environ, "PORT": str(FRONTEND_PORT), "BROWSER": "none",
               "WATCHPACK_POLLING": "true", "CI": "false"}
        components.append(Component(
            "frontend", [str(react_scripts), "start"], FRONTEND_DIR, env,
            f"{FRONTEND_ORIGIN}/"))
    return components


def run_supervisor(*, with_backend: bool, with_frontend: bool) -> int:
    """Foreground supervisor loop (also the detached child of ``start``)."""
    lab.ensure_dirs()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    components = build_components(with_backend=with_backend, with_frontend=with_frontend)
    PID_PATH.write_text(str(os.getpid()) + "\n")
    stopping = {"now": False}

    def _stop(_signum, _frame):
        stopping["now"] = True

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    log(f"supervisor: pid={os.getpid()} supervising {[c.name for c in components]}")

    for component in components:
        component.start()

    last_gateway_check = time.time()
    try:
        while not stopping["now"]:
            for component in components:
                if component.proc is None:
                    component.start()
                    continue
                code = component.proc.poll()
                if code is None:
                    continue
                component.last_exit_code = code
                delay = component.restart_delay()
                log(f"{component.name}: exited rc={code} — restarting in {delay:.0f}s")
                slept = 0.0
                while slept < delay and not stopping["now"]:
                    time.sleep(0.5)
                    slept += 0.5
                if stopping["now"]:
                    break
                component.restarts += 1
                component.start()
            if stopping["now"]:
                break
            if time.time() - last_gateway_check >= GATEWAY_REPAIR_INTERVAL:
                last_gateway_check = time.time()
                try:
                    ensure_gateway_upstreams()
                except Exception as exc:  # noqa: BLE001 — never fail the loop
                    log(f"gateway watchdog: {type(exc).__name__}: {exc}")
            write_status({
                "state": "running",
                "supervisor_pid": os.getpid(),
                "components": {c.name: c.status() for c in components},
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            })
            time.sleep(POLL_SECONDS)
    finally:
        for component in components:
            component.stop()
        write_status({
            "state": "stopped",
            "supervisor_pid": os.getpid(),
            "components": {c.name: c.status() for c in components},
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        })
        try:
            if read_pid() == os.getpid():
                PID_PATH.unlink()
        except OSError:
            pass
        log("supervisor: stopped")
    return 0


# --- commands --------------------------------------------------------------


def _port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _port_conflicts(*, with_backend: bool, with_frontend: bool) -> list[str]:
    conflicts = []
    if with_backend and _port_in_use(lab.BACKEND_PORT):
        conflicts.append(f"127.0.0.1:{lab.BACKEND_PORT} (release backend)")
    if with_frontend and _port_in_use(FRONTEND_PORT):
        conflicts.append(f"127.0.0.1:{FRONTEND_PORT} (frontend dev server)")
    return conflicts


def _await(ready, *, timeout: float, poll: float) -> dict:
    deadline = time.time() + timeout
    payload = health_report()
    while time.time() < deadline:
        if ready(payload):
            return payload
        pid = read_pid()
        if not (pid and process_alive(pid)):
            break  # supervisor is gone — do not wait for something that died
        time.sleep(poll)
        payload = health_report()
    return payload


def command_start(args) -> int:
    lab.ensure_dirs()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    running = read_pid()
    if running and process_alive(running):
        print(f"supervisor already running (pid={running}) — nothing to start")
        payload = health_report()
        print_status(payload)
        return 0 if payload["healthy"] else 1

    with_backend = not args.no_backend
    with_frontend = not args.no_frontend

    ensure_containers()
    gateway = ensure_gateway_upstreams()
    for route in gateway["unreachable"]:
        print(f"gateway repair: {route}")
    if gateway["unreachable"] and not gateway["repaired"]:
        print("WARNING — lab gateway still cannot reach its upstreams; "
              "check the Supabase stack containers")

    conflicts = _port_conflicts(with_backend=with_backend, with_frontend=with_frontend)
    if conflicts:
        if not args.takeover:
            print("BLOCKED — these ports are already served by an unsupervised "
                  "process:")
            for conflict in conflicts:
                print(f"  {conflict}")
            print("Re-run with --takeover to stop the Demo Lab's own leftover "
                  "backend/frontend processes, or stop them yourself.")
            return 1
        for entry in stop_unsupervised_lab_processes():
            print(f"takeover: stopped {entry}")

    argv = [sys.executable, str(pathlib.Path(__file__).resolve()), "run"]
    if args.no_backend:
        argv.append("--no-backend")
    if args.no_frontend:
        argv.append("--no-frontend")

    console = LOG_DIR / "supervisor.console.log"
    with open(os.devnull, "rb") as devnull, console.open("ab") as out:
        subprocess.Popen(argv, cwd=str(REPO_ROOT), stdin=devnull, stdout=out,
                         stderr=subprocess.STDOUT, start_new_session=True,
                         close_fds=True)
    print(f"supervisor launched (detached) — waiting up to {args.wait:.0f}s for health")

    def ready(payload: dict) -> bool:
        probes = payload["probes"]
        backend_ok = probes["backend"]["ok"] if with_backend else True
        frontend_ok = probes["frontend"]["ok"] if with_frontend else True
        return bool(backend_ok and frontend_ok)

    payload = _await(ready, timeout=args.wait, poll=3.0)
    print_status(payload)
    return 0 if ready(payload) else 1


def command_stop(_args) -> int:
    pid = read_pid()
    if pid and process_alive(pid):
        print(f"stopping supervisor pid={pid}")
        os.kill(pid, signal.SIGTERM)
        deadline = time.time() + 40
        while time.time() < deadline and process_alive(pid):
            time.sleep(0.5)
        if process_alive(pid):
            print("supervisor did not exit in time — sending SIGKILL")
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    else:
        print("no supervised Demo Lab process was recorded as running")
    leftovers = stop_unsupervised_lab_processes()
    for entry in leftovers:
        print(f"stopped leftover {entry}")
    if not pid and not leftovers:
        print("nothing to stop")
    print("containers are left running (restart policy = unless-stopped); the next "
          "start reuses them")
    return 0


def command_restart(args) -> int:
    command_stop(args)
    time.sleep(1.0)
    return command_start(args)


def command_status(args) -> int:
    payload = health_report()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_status(payload)
    return 0 if payload["healthy"] else 1


def command_logs(args) -> int:
    targets = {"supervisor": SUPERVISOR_LOG,
               "backend": LOG_DIR / "backend.log",
               "frontend": LOG_DIR / "frontend.log"}
    names = [args.component] if args.component else list(targets)
    for name in names:
        path = targets.get(name)
        if path is None:
            print(f"unknown component: {name} (supervisor|backend|frontend)")
            return 2
        print(f"--- {name}: {path}")
        if not path.exists():
            print("    (no log yet)")
            continue
        for line in path.read_text(errors="replace").splitlines()[-args.lines:]:
            print(f"    {line}")
    return 0


def command_run(args) -> int:
    """Foreground supervisor — the detached child of ``start``."""
    existing = read_pid()
    if existing and existing != os.getpid() and process_alive(existing):
        print(f"another supervisor is already running (pid={existing})",
              file=sys.stderr)
        return 2
    if _port_conflicts(with_backend=not args.no_backend,
                       with_frontend=not args.no_frontend):
        print("BLOCKED — a Demo Lab port is already served by another process; "
              "run `stop` first", file=sys.stderr)
        return 2
    # At boot (systemd --user unit) the local Supabase containers return by
    # their own restart policy, but a stopped disposable lab container must be
    # started here. Idempotent; fail-closed when a required container is absent.
    if getattr(args, "ensure_containers", False):
        log(f"containers: {ensure_containers()}")
    return run_supervisor(with_backend=not args.no_backend,
                          with_frontend=not args.no_frontend)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Keep the local Demo Lab (release backend + frontend) "
                    "continuously available. Local only: never contacts "
                    "production, Render or hosted Supabase.")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="ensure containers, then start supervised")
    start.add_argument("--wait", type=float, default=300.0,
                       help="seconds to wait for backend+frontend health (default 300)")
    start.add_argument("--takeover", action="store_true",
                       help="stop the Demo Lab's own leftover backend/frontend "
                            "processes when their ports are already in use")
    start.add_argument("--no-backend", action="store_true")
    start.add_argument("--no-frontend", action="store_true")
    start.set_defaults(func=command_start)

    stop = sub.add_parser("stop", help="stop the supervisor and its children")
    stop.set_defaults(func=command_stop)

    restart = sub.add_parser("restart", help="stop, then start again")
    restart.set_defaults(func=command_restart, wait=300.0, takeover=True,
                         no_backend=False, no_frontend=False)

    status = sub.add_parser("status", help="health report (exit 1 unless healthy)")
    status.add_argument("--json", action="store_true", help="print the JSON report")
    status.set_defaults(func=command_status)

    logs = sub.add_parser("logs", help="tail the supervisor/backend/frontend logs")
    logs.add_argument("component", nargs="?",
                      choices=["supervisor", "backend", "frontend"])
    logs.add_argument("--lines", type=int, default=30)
    logs.set_defaults(func=command_logs)

    run = sub.add_parser("run", help=argparse.SUPPRESS)
    run.add_argument("--no-backend", action="store_true")
    run.add_argument("--no-frontend", action="store_true")
    run.add_argument("--ensure-containers", action="store_true",
                     help="start any stopped required lab container first "
                          "(used by the systemd --user unit at boot)")
    run.set_defaults(func=command_run)

    args = parser.parse_args()
    try:
        return args.func(args)
    except RuntimeError as exc:
        print(f"BLOCKED — {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())








