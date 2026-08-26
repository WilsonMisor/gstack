#!/usr/bin/env python3

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "PREOS-INTEGRATION.md"
HANDOFF_TMPL = ROOT / "preos-handoff" / "SKILL.md.tmpl"
HANDOFF = ROOT / "preos-handoff" / "SKILL.md"

for path in [DOC, HANDOFF_TMPL, HANDOFF]:
    if not path.is_file():
        print(f"FAIL: {path.relative_to(ROOT)} is missing")
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
    "gstack-preos-handoff",
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
    "do not route directly from planning to `gstack-ship`",
    "PREOS RECOVERY REQUIRED",
    "SAFE_TO_RESUME",
    "RECOVERY_CONFLICT",
    "Conversation memory is never authoritative execution state",
]
missing = [token for token in required if token not in text]
if missing:
    for token in missing:
        print(f"FAIL: PREOS integration contract missing semantic anchor: {token}")
    raise SystemExit(1)

handoff = HANDOFF_TMPL.read_text(encoding="utf-8")
for token in [
    "name: preos-handoff",
    "PREOS HANDOFF READY",
    "PREOS RECOVERY REQUIRED",
    "$preos-production-plan",
    "canonical AI Task Packet",
    "do not route directly from planning to `/ship`",
    "first unverified action",
    "gstack-context-restore",
]:
    if token not in handoff:
        print(f"FAIL: preos-handoff skill missing semantic anchor: {token}")
        raise SystemExit(1)

for prohibited in [
    "gstack authorizes production",
    "gstack may accept production risk",
    "PREOS state belongs under .gstack",
]:
    if prohibited in text or prohibited in handoff:
        print(f"FAIL: prohibited authority statement present: {prohibited}")
        raise SystemExit(1)

print("PASS: gstack PREOS specialist routing, governed planning handoff, continuity and authority boundaries are present")
