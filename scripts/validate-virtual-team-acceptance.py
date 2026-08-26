#!/usr/bin/env python3
"""Deterministic organizational acceptance audit for the three-repository upgrade.

This is a PLAN-TRIGGERED REMEDIATION for the Phase 15/21 gap: prove that the
integrated system still behaves as one virtual development organization with
separate authority, implementation, assurance, release, and recovery roles.

It deliberately does NOT claim that an authenticated external Codex/model ran.
That remains Phase 18 host evidence. This audit proves the repository-level
organizational contract and deterministic PREOS evidence/gate behavior.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"required file missing: {path}")
    return path.read_text(encoding="utf-8")


def run(cmd: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        fail(f"command failed with exit {proc.returncode}: {' '.join(cmd)}")
    return proc


def assert_organizational_contract(blueprint: Path, preos: Path, gstack: Path) -> None:
    reconciliation = read(blueprint / "orchestration" / "upgrade-reconciliation.md")
    lifecycle = read(preos / "docs" / "integrated-lifecycle.md")
    implement = read(preos / "preos-production-implement" / "SKILL.md")
    integration = read(gstack / "PREOS-INTEGRATION.md")
    existing_e2e = read(gstack / "scripts" / "validate-three-repo-acceptance.py")

    # Canonical ownership must stay split across the organization.
    for token in [
        "one canonical Project Contract",
        "one canonical 75-control baseline",
        "one canonical AI Task Packet",
        "one PREOS production runtime-state authority",
        "one accountable human production-approval boundary",
        "Conversation memory is never authoritative execution state",
    ]:
        require(token in reconciliation, f"Blueprint reconciliation missing ownership invariant: {token}")

    # PREOS must orchestrate independent assurance after bounded implementation.
    for token in ["Codex", "gstack-cso", "gstack-review", "gstack-qa", "G0", "G11"]:
        require(token.lower() in (lifecycle + "\n" + implement).lower(),
                f"PREOS lifecycle/implementation route missing organizational role: {token}")

    # gstack remains a specialist workforce, not production authority.
    for token in [
        "gstack-cso", "gstack-review", "gstack-qa", "gstack-benchmark",
        "gstack-ship", "gstack-land-and-deploy", "gstack-canary",
        "not an automatic PREOS GREEN result", "accountable human production approval",
    ]:
        require(token in integration, f"gstack integration missing specialist/authority anchor: {token}")

    forbidden = [
        "gstack authorizes production",
        "gstack may accept production risk",
        "PREOS state belongs under .gstack",
        "gstack Project Contract",
        "gstack 75-control baseline",
    ]
    for token in forbidden:
        require(token not in integration, f"authority collapse detected in gstack integration: {token}")

    # The existing Phase-15 fixture must remain explicit that its edit is only the
    # deterministic Codex boundary, never a claim of authenticated model execution.
    require("without claiming an\n        # authenticated external Codex model ran" in existing_e2e,
            "Phase-15 fixture lost its explicit no-fake-Codex boundary")
    for token in ["SESSION_INTERRUPTED", "SAFE_TO_RESUME", "A-PROD", "BLOCKED"]:
        require(token in existing_e2e, f"Phase-15 interruption/authority path missing: {token}")

    # Independent specialist and release skills must remain physically distinct.
    skills = {
        "review": gstack / "review" / "SKILL.md",
        "security": gstack / "cso" / "SKILL.md",
        "qa": gstack / "qa" / "SKILL.md",
        "performance": gstack / "benchmark" / "SKILL.md",
        "ship": gstack / "ship" / "SKILL.md",
        "deploy": gstack / "land-and-deploy" / "SKILL.md",
        "canary": gstack / "canary" / "SKILL.md",
    }
    contents: dict[str, str] = {}
    expected_names = {
        "review": "review", "security": "cso", "qa": "qa", "performance": "benchmark",
        "ship": "ship", "deploy": "land-and-deploy", "canary": "canary",
    }
    for role, path in skills.items():
        text = read(path)
        contents[role] = text
        require(f"name: {expected_names[role]}" in text, f"{role} specialist has wrong/missing skill identity")
    require(len({skills[r].resolve() for r in ["review", "security", "qa", "performance"]}) == 4,
            "review/security/QA/performance specialists collapsed to one file")

    # Release capability exists only after the human authority boundary in the
    # governed integration sequence.
    release = integration.partition("## Release relationship")[2]
    require(bool(release), "gstack integration missing release relationship")
    order = [
        "Blueprint launch readiness", "PREOS G0-G11 assurance",
        "accountable human production approval", "gstack-ship",
        "gstack-land-and-deploy", "gstack-canary",
    ]
    positions = [release.find(token) for token in order]
    require(all(p >= 0 for p in positions), "release sequence missing a required organizational boundary")
    require(positions == sorted(positions), "release sequence bypasses PREOS/human authority")

    print("PASS: organizational ownership and specialist independence")


def assert_specialist_evidence_and_gates(preos: Path) -> None:
    validate_evidence = preos / "scripts" / "validate-evidence.py"
    evaluate_gates = preos / "scripts" / "evaluate-gates.py"
    gates_spec = json.loads(read(preos / "references" / "gates" / "production-gates.json"))
    expected_gates = [f"G{i}" for i in range(12)]
    actual_gates = [g.get("id") for g in gates_spec.get("gates", [])]
    require(actual_gates == expected_gates, "canonical PREOS gate order is not exactly G0-G11")
    rules = gates_spec.get("rules", [])
    for rule in [
        "UNKNOWN never silently becomes GREEN",
        "HUMAN REVIEW cannot be self-approved by AI",
    ]:
        require(rule in rules, f"canonical PREOS gate rule missing: {rule}")

    with tempfile.TemporaryDirectory(prefix="virtual-team-acceptance-") as td:
        root = Path(td)
        evidence_dir = root / "evidence"
        evidence_dir.mkdir()
        produced_at = dt.datetime.now(dt.timezone.utc).isoformat()

        producers = {
            "E-SECURITY": "gstack-cso",
            "E-REVIEW": "gstack-review",
            "E-QA": "gstack-qa",
            "E-PERFORMANCE": "gstack-benchmark",
        }
        evidence_paths: list[Path] = []
        for evidence_id, producer in producers.items():
            artifact = evidence_dir / f"{evidence_id.lower()}.txt"
            artifact.write_text(f"deterministic organizational acceptance evidence from {producer}\n", encoding="utf-8")
            record = {
                "evidence_id": evidence_id,
                "requirement_ids": ["VTEAM-001"],
                "produced_at": produced_at,
                "producer": producer,
                "environment": "disposable-organizational-acceptance",
                "artifact_location": str(artifact),
                "validity": "CURRENT",
                "bindings": {
                    "purpose": "three-repository virtual-team acceptance",
                    "producer_role": producer,
                    "phase": "15/21-remediation",
                },
                "result": "PASS",
            }
            path = evidence_dir / f"{evidence_id}.json"
            path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            evidence_paths.append(path)

        validated = run([sys.executable, str(validate_evidence), *map(str, evidence_paths)], cwd=preos)
        require("PASS evidence: 4 record(s) structurally valid" in validated.stdout,
                "PREOS did not validate four separate specialist evidence records")

        # Bind specialist evidence to the complete G0-G11 chain. This does not
        # manufacture substantive production evidence; it tests deterministic gate
        # mechanics and separation using disposable acceptance records.
        gate_evidence = {
            "G0": ["E-REVIEW"], "G1": ["E-REVIEW"], "G2": ["E-REVIEW"],
            "G3": ["E-SECURITY"], "G4": ["E-QA"], "G5": ["E-REVIEW"],
            "G6": ["E-PERFORMANCE"], "G7": ["E-QA"], "G8": ["E-QA"],
            "G9": ["E-QA"], "G10": ["E-SECURITY"],
            "G11": ["E-SECURITY", "E-REVIEW", "E-QA", "E-PERFORMANCE"],
        }
        green_input = {
            "gates": {
                gid: [{
                    "state": "GREEN",
                    "evidence_ids": gate_evidence[gid],
                    "source": "virtual-team-organizational-acceptance",
                }]
                for gid in expected_gates
            }
        }
        green_path = root / "gates-green.json"
        green_out = root / "gates-green-out.json"
        green_path.write_text(json.dumps(green_input, indent=2) + "\n", encoding="utf-8")
        run([sys.executable, str(evaluate_gates), str(green_path), "--output", str(green_out)], cwd=preos)
        green = json.loads(read(green_out))["gate_results"]
        require(list(green) == expected_gates, "PREOS evaluator did not return exact G0-G11 sequence")
        require(all(green[g]["state"] == "GREEN" for g in expected_gates),
                "complete disposable evidence did not produce GREEN across G0-G11")

        # Missing evidence must degrade GREEN to UNKNOWN.
        missing_input = copy.deepcopy(green_input)
        missing_input["gates"]["G3"][0]["evidence_ids"] = []
        missing_path = root / "gates-missing.json"
        missing_out = root / "gates-missing-out.json"
        missing_path.write_text(json.dumps(missing_input, indent=2) + "\n", encoding="utf-8")
        run([sys.executable, str(evaluate_gates), str(missing_path), "--output", str(missing_out)], cwd=preos)
        missing = json.loads(read(missing_out))["gate_results"]
        require(missing["G3"]["state"] == "UNKNOWN",
                "missing security evidence silently remained GREEN")

        # A RED specialist/gate result must block by returning PREOS' blocking code.
        red_input = copy.deepcopy(green_input)
        red_input["gates"]["G6"][0]["state"] = "RED"
        red_path = root / "gates-red.json"
        red_out = root / "gates-red-out.json"
        red_path.write_text(json.dumps(red_input, indent=2) + "\n", encoding="utf-8")
        red_proc = run([sys.executable, str(evaluate_gates), str(red_path), "--output", str(red_out)], cwd=preos, check=False)
        require(red_proc.returncode == 2, "RED performance gate did not block with exit code 2")
        red = json.loads(read(red_out))["gate_results"]
        require(red["G6"]["state"] == "RED", "RED performance result was not preserved")

    print("PASS: separate specialist evidence feeds deterministic PREOS G0-G11")
    print("PASS: missing evidence becomes UNKNOWN and RED remains blocking")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True, type=Path)
    parser.add_argument("--preos", required=True, type=Path)
    parser.add_argument("--gstack", required=True, type=Path)
    args = parser.parse_args()
    blueprint = args.blueprint.resolve()
    preos = args.preos.resolve()
    gstack = args.gstack.resolve()
    assert_organizational_contract(blueprint, preos, gstack)
    assert_specialist_evidence_and_gates(preos)
    print("PASS: virtual-team organizational acceptance audit complete")


if __name__ == "__main__":
    main()
