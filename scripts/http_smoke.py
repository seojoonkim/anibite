#!/usr/bin/env python3
"""Exercise real loopback HTTP against a disposable, synthetic AniBite DB.

Run with the interpreter containing backend/requirements.txt dependencies.
No application modules are imported by this runner. Use --output-dir to keep
JSON results and the server log; otherwise all artifacts are temporary.
"""

import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from typing import Any, cast
import urllib.error
import urllib.request

BACKEND = Path(__file__).resolve().parents[1] / "backend"


def run_journey(tmp, output_dir):
    records = []
    checks = []
    result = {
        "checks": checks,
        "requests": records,
        "isolation": "allowlisted environment; synthetic temp DB seeded with demo_seed; localhost only; temp DB and process cleaned up",
    }

    def check(name, condition):
        checks.append({"name": name, "passed": bool(condition)})

    # Deliberately do not inherit credentials, .env settings, or a real DB path.
    env = {
        "PATH": os.defpath,
        "HOME": str(tmp),
        "TMPDIR": str(tmp),
        "PYTHONPATH": str(BACKEND),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "APP_ENV": "test",
        "SECRET_KEY": "synthetic-http-smoke-not-for-deployment-123456789",
        "DATABASE_PATH": str(tmp / "synthetic.sqlite"),
        "ADMIN_USER_IDS": "",
        "DEMO_PASSWORD": "Synthetic-HTTP-Only-Password-123",
    }
    log_path = output_dir / "http-server.log"
    server = None
    try:
        with log_path.open("w", encoding="utf-8") as log:
            subprocess.run(
                [sys.executable, "-m", "demo_seed", "--database", env["DATABASE_PATH"]],
                cwd=tmp, env=env, check=True, stdout=log, stderr=subprocess.STDOUT,
                timeout=60,
            )
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            base = f"http://127.0.0.1:{port}"
            result["base_url"] = base
            server = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
                cwd=tmp, env=env, stdout=log, stderr=subprocess.STDOUT,
            )
            # Ignore any inherited HTTP proxy: every request must stay local.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _ in range(100):
                try:
                    with opener.open(base + "/health", timeout=0.3) as response:
                        if response.status == 200:
                            break
                except (OSError, urllib.error.URLError):
                    if server.poll() is not None:
                        raise RuntimeError("server exited during startup")
                    time.sleep(0.1)
            else:
                raise RuntimeError("readiness timeout")

            token = ""

            def req(method, path, data=None, auth=False) -> tuple[int, Any]:
                headers = {"Content-Type": "application/json", "Origin": "http://localhost:5173"}
                if auth:
                    headers["Authorization"] = "Bearer " + token
                request = urllib.request.Request(
                    base + path,
                    data=None if data is None else json.dumps(data).encode(),
                    headers=headers, method=method,
                )
                try:
                    response = opener.open(request, timeout=10)
                except urllib.error.HTTPError as error:
                    response = error
                with response:
                    status = cast(int, response.status)
                    raw = response.read().decode()
                try:
                    body = json.loads(raw) if raw else None
                except ValueError:
                    body = raw[:300]
                safe = body
                if path == "/api/auth/login" and isinstance(body, dict):
                    safe = {key: value for key, value in body.items() if "token" not in key}
                records.append({"method": method, "path": path, "status": status, "body": safe})
                return status, body

            check("readiness", req("GET", "/ready") == (200, {"status": "ready"}))
            for path in ["/api/anime/?page=1&page_size=20", "/api/anime/10", "/api/characters/10", "/api/activities?limit=100", "/api/search?q=Synthetic"]:
                status, body = req("GET", path)
                check("public " + path, status == 200)
            status, body = req("GET", "/api/auth/me")
            check("anonymous auth guard", status in (401, 403))
            status, body = req("POST", "/api/ratings/", {"anime_id": 10, "rating": 4, "status": "RATED"})
            check("anonymous write guard", status in (401, 403))
            status, body = req("POST", "/api/auth/login", {"username": "anibitedemo", "password": "wrong-synthetic-password"})
            check("wrong password rejected", status == 401)
            status, body = req("POST", "/api/auth/login", {"username": "anibitedemo", "password": env["DEMO_PASSWORD"]})
            check("ordinary login", status == 200)
            token = body["access_token"]
            status, me = req("GET", "/api/auth/me", auth=True)
            check("authenticated identity", status == 200 and me["username"] == "anibitedemo")
            for kind, itemfield, singular in [("ratings", "anime_id", "anime"), ("character-ratings", "character_id", "character")]:
                prefix = "/api/" + kind
                status, created = req("POST", prefix + "/", {itemfield: 10, "rating": 4, "status": "RATED"}, True)
                check(kind + " create", status == 201)
                status, read = req("GET", prefix + "/" + singular + "/10", auth=True)
                check(kind + " create readback", status == 200 and read["rating"] == 4)
                activity_type = "anime_rating" if kind == "ratings" else "character_rating"
                path = f'/api/activities?activity_type={activity_type}&item_id=10&user_id={me["id"]}'
                status, acts = req("GET", path)
                check(kind + " one projection", status == 200 and acts["total"] == len(acts["items"]) == 1)
                activity = acts["items"][0]
                status, updated = req("POST", prefix + "/", {itemfield: 10, "rating": 5, "status": "RATED"}, True)
                check(kind + " update", status == 201 and updated["id"] == created["id"])
                status, read = req("GET", prefix + "/" + singular + "/10", auth=True)
                check(kind + " update readback", status == 200 and read["rating"] == 5)
                status, acts = req("GET", path)
                check(kind + " activity ID preserved", status == 200 and acts["total"] == len(acts["items"]) == 1 and acts["items"][0]["id"] == activity["id"] and acts["items"][0]["rating"] == 5)
                status, detail = req("GET", f'/api/activities/{activity["id"]}')
                check(kind + " activity detail readback", status == 200 and detail["rating"] == 5)
                status, listing = req("GET", prefix + "/me/all", auth=True)
                check(kind + " list readback", status == 200 and any(x.get(itemfield) == 10 and x["rating"] == 5 for x in listing["rated"]))
                status, body = req("DELETE", prefix + "/" + singular + "/10", auth=True)
                check(kind + " delete", status == 204)
                status, body = req("GET", prefix + "/" + singular + "/10", auth=True)
                check(kind + " deletion readback", status == 200 and body is None)
                status, acts = req("GET", path)
                check(kind + " projection removed", status == 200 and acts["total"] == len(acts["items"]) == 0)

            # Preserve the original observational probes; promote RATED-null to a gate.
            for path in ["/api/anime", "/api/anime/", "/api/characters/10", "/api/rating-pages/anime", "/api/rating-pages/characters", "/api/ratings/anime/1"]:
                req("GET", path)
            for kind, itemfield in [("ratings", "anime_id"), ("character-ratings", "character_id")]:
                for payload in [{itemfield: 11, "rating": None, "status": "RATED"}, {itemfield: 12, "rating": 4, "status": "INVALID_SYNTHETIC"}, {itemfield: 13, "rating": 4.2, "status": "RATED"}]:
                    status, body = req("POST", "/api/" + kind + "/", payload, True)
                    if payload["rating"] is None:
                        check(kind + " RATED-null rejected", status == 422)
                    singular = "anime" if kind == "ratings" else "character"
                    status, body = req("GET", "/api/" + kind + "/" + singular + "/" + str(payload[itemfield]), auth=True)
                    if payload["rating"] is None:
                        check(kind + " RATED-null not persisted", status == 200 and body is None)
            req("GET", "/api/characters/10", auth=True)
    except Exception as error:
        check("runner completed", False)
        result["error"] = f"{type(error).__name__}: {error}"
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    result["passed"] = sum(check["passed"] for check in checks)
    result["failed"] = sum(not check["passed"] for check in checks)
    (output_dir / "http-smoke.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "requests"}, ensure_ascii=False, indent=2))
    if result["failed"] and log_path.exists():
        print(log_path.read_text(encoding="utf-8"), file=sys.stderr)
    return 1 if result["failed"] else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Keep http-smoke.json and http-server.log in this directory (overwrites those files).")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="anibite-http-synthetic-") as temporary:
        tmp = Path(temporary)
        output_dir = args.output_dir.resolve() if args.output_dir else tmp / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        return run_journey(tmp, output_dir)


if __name__ == "__main__":
    sys.exit(main())
