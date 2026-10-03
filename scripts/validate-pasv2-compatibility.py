#!/usr/bin/env python3
"""Validate PAS v2 cross-repository compatibility bindings."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "integration" / "PASV2-COMPATIBILITY.json"
INTEGRATION = ROOT / "integration" / "INTEGRATION-MANIFEST.json"
WORKFLOW = ROOT / ".github" / "workflows" / "three-repo-acceptance.yml"
LEGACY_PIN_PREFIXES = {"0f81fb370", "166bb377"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing compatibility artifact: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        fail(f"git {' '.join(args)} failed for {repo}: {proc.stderr.strip()}")
    return proc.stdout.strip()


def validate_static() -> dict:
    manifest = load_json(MANIFEST)
    integration = load_json(INTEGRATION)
    workflow = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.is_file() else ""
    if not workflow:
        fail("three-repo acceptance workflow missing")
    for prefix in LEGACY_PIN_PREFIXES:
        if prefix in workflow:
            fail(f"workflow still contains stale PAS v2 compatibility pin prefix {prefix}")
    for prohibited in ["BLUEPRINT_CANDIDATE_SHA", "PREOS_CANDIDATE_SHA"]:
        if prohibited in workflow:
            fail(f"workflow still uses hard-coded candidate env var {prohibited}")
    for token in ["PASV2_COMPATIBILITY_MANIFEST", "BLUEPRINT_REF", "PREOS_REF", "validate-pasv2-compatibility.py"]:
        if token not in workflow:
            fail(f"workflow does not derive compatibility through manifest token: {token}")
    components = manifest.get("components", {})
    for key in ["blueprint", "preos", "gstack"]:
        item = components.get(key)
        if not item:
            fail(f"compatibility manifest missing component {key}")
        if not item.get("repository") or not item.get("ref") or not item.get("required_validators"):
            fail(f"compatibility component {key} is incomplete")
        if key in {"blueprint", "preos"} and (HEX40.match(item["ref"]) or any(item["ref"].startswith(prefix) for prefix in LEGACY_PIN_PREFIXES)):
            fail(f"compatibility component {key} must use a versioned branch/ref, not a stale hard SHA")
    if integration.get("current_compatibility_manifest") != "integration/PASV2-COMPATIBILITY.json":
        fail("integration manifest does not point at PASV2-COMPATIBILITY.json for current bindings")
    for gate, state in manifest.get("authority_boundary", {}).items():
        if state != "OPEN":
            fail(f"human gate {gate} must remain OPEN")
    return manifest


def validate_repo(repo: Path, validators: list[str], label: str) -> None:
    if not (repo / ".git").exists():
        fail(f"{label} checkout missing .git: {repo}")
    git(repo, "rev-parse", "--verify", "HEAD")
    for validator in validators:
        rel = validator.split()[0]
        if not (repo / rel).is_file():
            fail(f"{label} required validator missing: {rel}")


def validate_local_checkouts(manifest: dict, blueprint: Path | None, preos: Path | None, gstack: Path | None) -> None:
    repos = {"blueprint": blueprint, "preos": preos, "gstack": gstack}
    for key, repo in repos.items():
        if repo is None:
            continue
        item = manifest["components"][key]
        validate_repo(repo.resolve(), list(item["required_validators"]), key)
        if key in {"blueprint", "preos"}:
            branch = git(repo.resolve(), "branch", "--show-current")
            expected = item.get("ref")
            if branch and branch != expected:
                fail(f"{key} checkout branch drift: expected {expected}, got {branch}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--preos", type=Path)
    parser.add_argument("--gstack", type=Path)
    args = parser.parse_args()
    manifest = validate_static()
    validate_local_checkouts(manifest, args.blueprint, args.preos, args.gstack)
    print("PASS: PAS v2 compatibility manifest and workflow bindings are current and non-circular")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())