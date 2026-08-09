#!/usr/bin/env python3
"""Synchronize vetted upstream MRS files without executing upstream content."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "upstreams.json"
LOCK_PATH = ROOT / "sources.lock.json"
ALLOWED_HOSTS = {"raw.githubusercontent.com"}


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def download(url: str, min_bytes: int) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"unapproved upstream URL: {url}")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "cross-border-finance-rules-sync/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
        content_type = response.headers.get_content_type()
    lowered = data[:256].lstrip().lower()
    if len(data) < min_bytes:
        raise ValueError(f"upstream payload is too small: {len(data)} < {min_bytes}")
    if lowered.startswith((b"<!doctype", b"<html", b"{", b"[")):
        raise ValueError(f"upstream returned an error/document payload ({content_type})")
    return data


def safe_destination(relative: str) -> Path:
    destination = (ROOT / relative).resolve()
    if ROOT.resolve() not in destination.parents:
        raise ValueError(f"destination escapes repository: {relative}")
    return destination


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as temp_file:
            temp_file.write(data)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> None:
    config = load_json(CONFIG_PATH, {})
    previous = load_json(LOCK_PATH, {"schema": 1, "upstreams": []})
    previous_by_name = {item["name"]: item for item in previous.get("upstreams", [])}
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lock_entries = []

    for source in config.get("upstreams", []):
        name = source["name"]
        data = download(source["url"], int(source["min_bytes"]))
        destination = safe_destination(source["destination"])
        digest = hashlib.sha256(data).hexdigest()
        existing = destination.read_bytes() if destination.exists() else None
        changed = existing != data
        if changed:
            atomic_write(destination, data)
        prior = previous_by_name.get(name, {})
        updated_at = now if changed or prior.get("sha256") != digest else prior.get("updated_at", now)
        lock_entries.append(
            {
                "name": name,
                "url": source["url"],
                "destination": source["destination"],
                "size": len(data),
                "sha256": digest,
                "updated_at": updated_at,
            }
        )
        print(f"{name}: {len(data)} bytes sha256={digest} changed={changed}")

    rendered = (json.dumps({"schema": 1, "upstreams": lock_entries}, indent=2) + "\n").encode()
    if not LOCK_PATH.exists() or LOCK_PATH.read_bytes() != rendered:
        atomic_write(LOCK_PATH, rendered)


if __name__ == "__main__":
    main()

