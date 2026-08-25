#!/usr/bin/env python3

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "PREOS-INTEGRATION.md"

if not DOC.is_file():
    print("FAIL: PREOS-INTEGRATION.md is missing")
    raise SystemExit(1)

text = DOC.read_text(encoding="utf-8")
required = [
    "WilsonMisor/PREOS",
    "WilsonMisor/wed_dev_skill",
    "AI Product Delivery Blueprint",
    "PREOS determines required production-assurance",
    "gstack supplies specialist engineering review",
    "Codex implements approved bounded AI Task Packets",
    "Accountable humans accept consequential risk and authorize production",
    "gstack-plan-eng-review",
    "gstack-cso",
    "gstack-review",
    "gstack-investigate",
    "gstack-qa",
    "gstack-qa-only",
    "gstack-benchmark",
    "gstack-ship",
    "gstack-land-and-deploy",
    "gstack-canary",
    "gstack-retro",
    "Project Contract",
    "risk IDs and control IDs",
    "G0-G11",
    "not an automatic PREOS GREEN result",
    "must not become the PREOS source of truth",
    "PREOS_STATE_ROOT",
    "GSTACK_STATE_ROOT",
    "accountable human production approval",
]

missing = [token for token in required if token not in text]
if missing:
    for token in missing:
        print(f"FAIL: PREOS integration contract missing semantic anchor: {token}")
    raise SystemExit(1)

for prohibited in [
    "gstack authorizes production",
    "gstack may accept production risk",
    "PREOS state belongs under .gstack",
]:
    if prohibited in text:
        print(f"FAIL: prohibited authority statement present: {prohibited}")
        raise SystemExit(1)

print("PASS: gstack PREOS specialist routing and authority boundaries are present")
