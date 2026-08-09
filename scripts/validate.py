#!/usr/bin/env python3
"""Validate the hardcoded fallback and synchronized upstream artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FALLBACK = ROOT / "rules" / "cross-border-finance-fallback.yaml"
LOCK_PATH = ROOT / "sources.lock.json"
DOMAIN_RE = re.compile(r"^  - '\+\.([a-z0-9](?:[a-z0-9.-]*[a-z0-9])?)'$", re.ASCII)
REQUIRED = [
    "americanexpress.com",
    "sc.com",
    "standardchartered.com",
    "n26.com",
    "ifastcorp.com",
    "ifastglobalbank.com",
    "paypal.com",
    "bybit.eu",
    "bybit.com",
    "bybit-global.com",
    "okx.com",
    "okex.com",
    "binance.com",
    "t-mobile.com",
    "o2.co.uk"
]


def validate_fallback() -> list[str]:
    lines = FALLBACK.read_text(encoding="utf-8").splitlines()
    if "payload:" not in lines:
        raise ValueError("fallback is missing top-level payload")
    domains = []
    for number, line in enumerate(lines, 1):
        if not line.startswith("  - "):
            continue
        match = DOMAIN_RE.fullmatch(line)
        if not match:
            raise ValueError(f"invalid domain rule at line {number}: {line}")
        domain = match.group(1)
        if ".." in domain:
            raise ValueError(f"invalid domain at line {number}: {domain}")
        domains.append(domain)
    duplicates = sorted({domain for domain in domains if domains.count(domain) > 1})
    if duplicates:
        raise ValueError(f"duplicate domains: {duplicates}")
    if len(domains) < 390:
        raise ValueError(f"fallback unexpectedly small: {len(domains)}")
    missing = sorted(set(REQUIRED) - set(domains))
    if missing:
        raise ValueError(f"required fallback domains are missing: {missing}")
    print(f"fallback: {len(domains)} unique domain suffixes")
    return domains


def validate_upstreams() -> None:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    entries = lock.get("upstreams", [])
    if len(entries) != 2:
        raise ValueError(f"expected 2 synchronized upstreams, got {len(entries)}")
    for entry in entries:
        path = (ROOT / entry["destination"]).resolve()
        if ROOT.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"missing or unsafe upstream artifact: {entry['destination']}")
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != entry["size"] or digest != entry["sha256"]:
            raise ValueError(f"lock mismatch for {entry['name']}")
        if data[:256].lstrip().lower().startswith((b"<!doctype", b"<html", b"{", b"[")):
            raise ValueError(f"invalid upstream artifact: {entry['name']}")
        print(f"{entry['name']}: {len(data)} bytes sha256={digest}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-upstreams", action="store_true")
    args = parser.parse_args()
    validate_fallback()
    if args.require_upstreams:
        validate_upstreams()


if __name__ == "__main__":
    main()

