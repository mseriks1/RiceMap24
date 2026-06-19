#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

BASE_URL = "http://127.0.0.1:8091"
TIMEOUT_SECONDS = 8
ENDPOINTS = [
    "/health",
    "/",
    "/list",
    "/pricing",
    "/for-cooks",
    "/admin",
    "/api/cuisines",
    "/api/listings",
    "/styles.css?v=9380",
    "/app.js?v=9380",
]


def fetch(path: str) -> tuple[int, int, float, str]:
    url = BASE_URL + path
    start = time.perf_counter()
    try:
        with urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
            elapsed = time.perf_counter() - start
            content_type = response.headers.get("content-type", "")
            return response.status, len(body), elapsed, content_type
    except HTTPError as exc:
        elapsed = time.perf_counter() - start
        return exc.code, 0, elapsed, ""
    except URLError as exc:
        raise RuntimeError(f"Could not reach {url}. Is the API running on port 8091? {exc}") from exc


def main() -> int:
    failures: list[str] = []
    print("RiceMap24 local smoke test")
    print(f"Base URL: {BASE_URL}\n")
    for path in ENDPOINTS:
        try:
            status, size, elapsed, content_type = fetch(path)
        except Exception as exc:
            failures.append(f"{path}: {exc}")
            print(f"FAIL {path:<24} {exc}")
            continue
        ok = 200 <= status < 400 and size > 0
        if not ok:
            failures.append(f"{path}: status={status}, bytes={size}")
        label = "OK" if ok else "FAIL"
        print(f"{label:<4} {path:<24} status={status:<3} bytes={size:<8} time={elapsed:.2f}s type={content_type}")

    try:
        with urlopen(BASE_URL + "/health", timeout=TIMEOUT_SECONDS) as response:
            health = json.loads(response.read().decode("utf-8"))
        print("\nHealth summary:")
        for key in [
            "version",
            "env",
            "persistent_data_dir_set",
            "user_data_outside_code_dir",
            "database_inside_code_dir",
            "uploads_inside_code_dir",
            "demo_seed_allowed",
            "legacy_admin_key_available",
        ]:
            print(f"- {key}: {health.get(key)}")
    except Exception as exc:
        failures.append(f"health-json: {exc}")

    if failures:
        print("\nSmoke test failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("\nSmoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
