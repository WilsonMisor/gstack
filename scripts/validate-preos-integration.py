#!/usr/bin/env python3

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "PREOS-INTEGRATION.md"
HANDOFF_TMPL = ROOT / "preos-handoff" / "SKILL.md.tmpl"
HANDOFF = ROOT / "preos-handoff" / "SKILL.md"
AUTOPLAN_TMPL = ROOT / "autoplan" / "SKILL.md.tmpl"
AUTOPLAN = ROOT / "autoplan" / "SKILL.md"
RESTORE_TMPL = ROOT / "context-restore" / "SKILL.md.tmpl"
RESTORE = ROOT / "context-restore" / "SKILL.md"
SAVE_TMPL = ROOT / "context-save" / "SKILL.md.tmpl"
SAVE = ROOT / "context-save" / "SKILL.md"

for path in [DOC, HANDOFF_TMPL, HANDOFF, AUTOPLAN_TMPL, AUTOPLAN, RESTORE_TMPL, RESTORE, SAVE_TMPL, SAVE]:
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
    "adr_ids",
    "risk_ids",
    "control_ids",
    "gate:",
    "task_packet",
    "architecture_binding",
    "threat_context",
    "known_exceptions",
    "mutation_permission",
    "required_evidence",
    "finding_ids",
    "reproduction_or_test_steps",
    "changed_files_if_authorized",
    "remaining_uncertainty",
    "acceptance_result",
    "Deployment ability is not deployment authority",
]:
    if token not in handoff:
        print(f"FAIL: preos-handoff skill missing semantic anchor: {token}")
        raise SystemExit(1)

# The tracked generated Claude skill must reflect the template contract rather
# than leaving the stronger semantics only in source templates.
generated_handoff = HANDOFF.read_text(encoding="utf-8")
for token in ["PREOS HANDOFF READY", "risk_ids", "required_evidence", "finding_ids", "Deployment ability is not deployment authority"]:
    if token not in generated_handoff:
        print(f"FAIL: generated preos-handoff skill is stale/missing: {token}")
        raise SystemExit(1)

autoplan_text = AUTOPLAN_TMPL.read_text(encoding="utf-8") + "\n" + AUTOPLAN.read_text(encoding="utf-8")
for token in [
    "## Governed implementation handoff",
    "gstack-preos-handoff",
    "$preos-production-plan",
    "do **not** route directly to `/ship`",
    "canonical Blueprint AI Task Packet -> Codex",
    "accountable human production approval",
]:
    if token not in autoplan_text:
        print(f"FAIL: autoplan governed handoff missing semantic anchor: {token}")
        raise SystemExit(1)

restore_text = RESTORE_TMPL.read_text(encoding="utf-8") + "\n" + RESTORE.read_text(encoding="utf-8")
for token in [
    "### Governed implementation resume gate",
    "PREOS RECOVERY REQUIRED",
    "SAFE_TO_RESUME",
    "BLOCKED",
    "RECOVERY_CONFLICT",
    "first unverified action",
    "Git/PREOS/Project Contract truth wins",
    "Restored semantic context is supplementary",
]:
    if token not in restore_text:
        print(f"FAIL: context-restore PREOS continuity routing missing semantic anchor: {token}")
        raise SystemExit(1)

save_template = SAVE_TMPL.read_text(encoding="utf-8")
generated_save = SAVE.read_text(encoding="utf-8")
for label, save_text in [("template", save_template), ("generated", generated_save)]:
    for token in [
        "supplementary semantic",
        "never authoritative execution state",
        "SAFE_TO_RESUME",
        "PREOS deterministic recovery",
        "Git, approved Blueprint artifacts",
    ]:
        if token not in save_text:
            print(f"FAIL: context-save {label} continuity boundary missing semantic anchor: {token}")
            raise SystemExit(1)
    for prohibited_save in [
        "full working context",
        "can resume without losing a beat",
        "pick up without losing a beat",
    ]:
        if prohibited_save in save_text:
            print(f"FAIL: context-save {label} still implies authoritative automatic resume: {prohibited_save}")
            raise SystemExit(1)

for prohibited in [
    "gstack authorizes production",
    "gstack may accept production risk",
    "PREOS state belongs under .gstack",
    "gstack Project Contract",
    "gstack 75-control baseline",
]:
    if prohibited in text or prohibited in handoff or prohibited in autoplan_text or prohibited in restore_text or prohibited in save_template or prohibited in generated_save:
        print(f"FAIL: prohibited authority statement present: {prohibited}")
        raise SystemExit(1)

print("PASS: gstack PREOS specialist routing, governed autoplan handoff, deterministic recovery routing and authority boundaries are present")
