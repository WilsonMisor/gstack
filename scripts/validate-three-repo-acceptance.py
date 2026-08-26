#!/usr/bin/env python3
"""Derived acceptance harness for the three-repository upgrade.

This file is not canonical product, contract, risk, control, task, approval, or
runtime state. It validates ownership invariants across checked-out candidate
repositories and runs a disposable non-WordPress lifecycle/recovery drill.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
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
        fail(f"required acceptance input is missing: {path}")
    return path.read_text(encoding="utf-8")


def run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        fail(f"command failed with exit {proc.returncode}: {' '.join(cmd)}")
    return proc


def git(repo: Path, *args: str) -> str:
    return run(["git", *args], cwd=repo).stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_cross_repo_invariants(blueprint: Path, preos: Path, gstack: Path) -> None:
    reconciliation = read(blueprint / "orchestration" / "upgrade-reconciliation.md")
    blueprint_skill = read(blueprint / "SKILL.md")
    blueprint_continuity = read(blueprint / "references" / "core" / "session-continuity.md")
    preos_skill = read(preos / "SKILL.md")
    preos_continuity = read(preos / "docs" / "session-continuity.md")
    preos_overlay = read(preos / "references" / "wordpress" / "wordpress-75-control-overlay.md")
    gstack_integration = read(gstack / "PREOS-INTEGRATION.md")
    gstack_handoff = read(gstack / "preos-handoff" / "SKILL.md")
    gstack_restore = read(gstack / "context-restore" / "SKILL.md")

    for token in [
        "one canonical Project Contract",
        "one canonical 75-control baseline",
        "one canonical AI Task Packet",
        "one PREOS production runtime-state authority",
        "one accountable human production-approval boundary",
        "Conversation memory is never authoritative execution state",
    ]:
        require(token in reconciliation, f"reconciliation register missing invariant: {token}")

    for token in ["AI Task Packet", "Blueprint", "Codex", "human"]:
        require(token.lower() in blueprint_skill.lower(), f"Blueprint skill missing ownership anchor: {token}")
    require("Conversation memory is never authoritative execution state" in blueprint_continuity,
            "Blueprint continuity does not reject conversation memory as authority")

    for token in [
        "PREOS_STATE_ROOT",
        "75",
        "G0",
        "G11",
        "RECOVERY_CONFLICT",
        "first unverified action",
        "UNKNOWN never silently becomes GREEN",
    ]:
        require(token in preos_skill, f"PREOS skill missing authority/recovery anchor: {token}")
    for token in ["SAFE_TO_RESUME", "BLOCKED", "RECOVERY_CONFLICT"]:
        require(token in preos_continuity, f"PREOS continuity missing state: {token}")

    import re
    mapped = re.findall(r"\| (FS-\d{3}) \|", preos_overlay)
    expected = [f"FS-{n:03d}" for n in range(1, 76)]
    require(mapped == expected and len(set(mapped)) == 75,
            "WordPress overlay must map canonical FS-001 through FS-075 exactly once")

    for token in [
        "PREOS_STATE_ROOT",
        "accountable human production approval",
        "PREOS RECOVERY REQUIRED",
        "not an automatic PREOS GREEN result",
    ]:
        require(token in gstack_integration, f"gstack integration contract missing boundary: {token}")
    for token in ["canonical AI Task Packet", "$preos-production-plan", "Deployment ability is not deployment authority"]:
        require(token in gstack_handoff, f"gstack handoff missing governed route: {token}")
    for token in ["SAFE_TO_RESUME", "BLOCKED", "RECOVERY_CONFLICT", "first unverified action"]:
        require(token in gstack_restore, f"gstack restore missing PREOS recovery route: {token}")

    combined_gstack = "\n".join([gstack_integration, gstack_handoff, gstack_restore])
    for forbidden in [
        "gstack authorizes production",
        "gstack may accept production risk",
        "PREOS state belongs under .gstack",
        "gstack Project Contract",
        "gstack 75-control baseline",
    ]:
        require(forbidden not in combined_gstack, f"gstack contains prohibited authority statement: {forbidden}")

    release_order = [
        "Blueprint readiness",
        "PREOS G0-G11",
        "accountable human production approval",
        "gstack-ship",
        "gstack-land-and-deploy",
        "gstack-canary",
    ]
    positions = [gstack_integration.find(token) for token in release_order]
    require(all(position >= 0 for position in positions), "gstack integration contract is missing release-order anchors")
    require(positions == sorted(positions), "release order differs from Blueprint -> PREOS -> human -> ship -> deploy -> canary")

    print("PASS: cross-repository ownership and release invariants")


def disposable_non_wordpress_e2e(blueprint: Path, preos: Path, gstack: Path) -> None:
    source_intake = blueprint / "scripts" / "source_intake.py"
    preos_scripts = preos / "scripts"

    with tempfile.TemporaryDirectory(prefix="three-repo-acceptance-") as td:
        base = Path(td)
        app = base / "application"
        app.mkdir()

        requirements = app / "requirements.md"
        requirements.write_text(
            "REQ-1: The service must return a deterministic greeting and remain governed by human production approval.\n",
            encoding="utf-8",
        )
        code = app / "app.py"
        code.write_text("print('hello v1')\n", encoding="utf-8")

        decisions = base / "source-decisions.json"
        decisions.write_text(json.dumps({
            "project_mode": "BROWNFIELD",
            "source_decisions": [
                {"path": "requirements.md", "authority": "HUMAN_APPROVED", "status": "CURRENT"},
                {"path": "app.py", "authority": "IMPLEMENTATION_EVIDENCE", "status": "CURRENT"},
            ],
            "source_requirements": [{
                "source_path": "requirements.md",
                "source_location": "line 1",
                "original_wording": "The service must return a deterministic greeting and remain governed by human production approval.",
                "normalized_interpretation": "Return deterministic greeting; production remains human-authorized.",
                "category": "FUNCTIONAL_AND_GOVERNANCE",
                "authority": "HUMAN_APPROVED",
                "confidence": "HIGH",
                "conflict_state": "NONE",
            }],
            "observed_architecture": {"runtime": "Python CLI"},
            "declared_architecture": {"runtime": "Python CLI"},
            "approved_architecture": {"runtime": "Python CLI"},
            "observed_stack": {"language": "Python"},
            "declared_stack": {"language": "Python"},
            "approved_stack": {"language": "Python"},
            "unknowns": [],
            "assumptions": [],
            "role_gaps": [],
            "human_decisions_required": [],
        }, indent=2) + "\n", encoding="utf-8")

        run([
            sys.executable, str(source_intake), str(app),
            "--project-root", str(app),
            "--decisions", str(decisions),
            "--intent", "three-repository disposable non-WordPress acceptance",
        ], cwd=blueprint)

        intake_root = app / ".ai-product-delivery" / "source-intake"
        intake = json.loads(read(intake_root / "SOURCE-INTAKE.json"))
        require(intake.get("project_mode") == "BROWNFIELD", "Blueprint intake did not classify disposable app as BROWNFIELD")
        require(len(intake.get("source_requirements", [])) == 1, "Blueprint intake did not preserve exactly one governed source requirement")
        require(not any(c.get("blocking") for c in intake.get("source_conflicts", [])), "Blueprint intake unexpectedly produced a blocking source conflict")

        contract_dir = app / ".ai-product-delivery" / "project-contract"
        packet_dir = app / ".ai-product-delivery" / "task-packets"
        contract_dir.mkdir(parents=True)
        packet_dir.mkdir(parents=True)
        contract = contract_dir / "PROJECT-CONTRACT.json"
        contract.write_text(json.dumps({
            "project_id": "three-repo-nonwp",
            "project_contract_version": "PC-1",
            "source_hashes": [{"artifact": "requirements.md", "sha256": sha256(requirements)}],
            "classification": {"profiles": ["software"], "production_assurance": "standard"},
        }, indent=2) + "\n", encoding="utf-8")
        packet = packet_dir / "TP-001.md"
        packet.write_text(
            "# TP-001\n\nApproved bounded scope: edit app.py only. Required tests: deterministic greeting. Production authorization: human only.\n",
            encoding="utf-8",
        )
        agents_template = read(blueprint / "templates" / "application-agents-continuity.md")
        (app / "AGENTS.md").write_text(agents_template, encoding="utf-8")

        git(app, "init")
        git(app, "config", "user.email", "three-repo-acceptance@example.invalid")
        git(app, "config", "user.name", "Three Repo Acceptance")
        git(app, "add", ".")
        git(app, "commit", "-m", "governed disposable baseline")

        env = os.environ.copy()
        env["PREOS_STATE_ROOT"] = str(base / "preos-state")

        run([sys.executable, str(preos_scripts / "init-project-state.py"), "three-repo-nonwp", "--repo", str(app)], cwd=preos, env=env)

        # Deterministic bounded implementation fixture. This exercises the exact
        # filesystem boundary that an approved Codex task packet is allowed to
        # mutate without pretending an authenticated model ran inside CI.
        code.write_text("print('hello v2')\n", encoding="utf-8")
        run([
            sys.executable, str(preos_scripts / "checkpoint-state.py"),
            "three-repo-nonwp", "--repo", str(app), "--kind", "soft",
            "--event", "SESSION_INTERRUPTED",
            "--project-contract", str(contract), "--project-contract-version", "PC-1",
            "--task-packet", str(packet), "--task-packet-id", "TP-001",
            "--last-verified-action", "bounded app.py edit durably captured",
            "--next-unverified-action", "deterministic greeting test",
            "--pending-test", "nonwp:greeting",
        ], cwd=preos, env=env)

        recovered = run([
            sys.executable, str(preos_scripts / "recover-state.py"),
            "three-repo-nonwp", "--repo", str(app),
        ], cwd=preos, env=env)
        recovery = json.loads(recovered.stdout)
        require(recovery.get("status") == "SAFE_TO_RESUME", "fresh-process PREOS recovery did not return SAFE_TO_RESUME")
        require(recovery.get("next_unverified_action") == "re-run uncertain test: nonwp:greeting",
                "PREOS did not resume from the first uncertain test")

        result = run([sys.executable, str(code)], cwd=app)
        require(result.stdout.strip() == "hello v2", "disposable bounded implementation verification failed")

        git(app, "add", "app.py")
        git(app, "commit", "-m", "verified bounded implementation")
        hard = run([
            sys.executable, str(preos_scripts / "checkpoint-state.py"),
            "three-repo-nonwp", "--repo", str(app), "--kind", "hard",
            "--event", "IMPLEMENTATION_COMPLETE",
            "--project-contract", str(contract), "--project-contract-version", "PC-1",
            "--task-packet", str(packet), "--task-packet-id", "TP-001",
            "--last-verified-action", "bounded implementation and required test verified",
            "--next-unverified-action", "independent gstack specialist assurance",
        ], cwd=preos, env=env)
        require("HARD CHECKPOINT" in hard.stdout, "PREOS did not create the verified Git-bound hard checkpoint")

        # gstack's actual specialist behavior is independently exercised by its
        # own review, CSO, QA, benchmark, and eval suites. Here we prove that the
        # cross-suite route is present and remains subordinate to PREOS/humans.
        gstack_contract = read(gstack / "PREOS-INTEGRATION.md")
        for route in ["gstack-review", "gstack-cso", "gstack-qa", "gstack-benchmark"]:
            require(route in gstack_contract, f"disposable lifecycle missing specialist assurance route: {route}")

        run([
            sys.executable, str(preos_scripts / "record-approval.py"),
            "three-repo-nonwp", "A-PROD", "--status", "PENDING",
            "--scope", "production authorization",
            "--authority", "Accountable Product Owner",
        ], cwd=preos, env=env)
        run([
            sys.executable, str(preos_scripts / "checkpoint-state.py"),
            "three-repo-nonwp", "--repo", str(app), "--kind", "soft",
            "--event", "APPROVAL_REQUIRED",
            "--project-contract", str(contract), "--project-contract-version", "PC-1",
            "--task-packet", str(packet), "--task-packet-id", "TP-001",
            "--required-approval", "A-PROD",
            "--last-verified-action", "implementation assurance ready for production gate",
            "--next-unverified-action", "human production authorization",
        ], cwd=preos, env=env)
        blocked = run([
            sys.executable, str(preos_scripts / "recover-state.py"),
            "three-repo-nonwp", "--repo", str(app),
        ], cwd=preos, env=env, check=False)
        require(blocked.returncode == 3, "pending human production approval did not block recovery")
        blocked_state = json.loads(blocked.stdout)
        require(blocked_state.get("status") == "BLOCKED", "pending human production approval was not preserved as BLOCKED")
        require(blocked_state.get("pending_approvals") == ["A-PROD"], "pending human approval identity did not survive")

        print("PASS: disposable non-WordPress Blueprint -> PREOS -> gstack/Codex-boundary lifecycle and interruption recovery")
        print("PASS: production remains BLOCKED pending accountable human authorization")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True, type=Path)
    parser.add_argument("--preos", required=True, type=Path)
    parser.add_argument("--gstack", required=True, type=Path)
    args = parser.parse_args()

    blueprint = args.blueprint.resolve()
    preos = args.preos.resolve()
    gstack = args.gstack.resolve()

    assert_cross_repo_invariants(blueprint, preos, gstack)
    disposable_non_wordpress_e2e(blueprint, preos, gstack)
    print("PASS: three-repository derived acceptance harness complete")


if __name__ == "__main__":
    main()
