#!/usr/bin/env python3
"""Validate PAS v2 cross-repository compatibility bindings."""
from __future__ import annotations

import argparse
import ast
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "integration" / "PASV2-COMPATIBILITY.json"
INTEGRATION = ROOT / "integration" / "INTEGRATION-MANIFEST.json"
WORKFLOW = ROOT / ".github" / "workflows" / "three-repo-acceptance.yml"
LEGACY_PIN_PREFIXES = {"0f81fb370", "166bb377"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
CONTRACT_VERSION = 'pasv2-implementation-first-v1'
HUMAN_GATES = {'PREOS_MODEL2_CROSSWALK_APPROVAL','GSTACK_WINDOWS_BROAD_SUITE_BACKLOG_DISPOSITION','PRODUCTION_RELEASE_AUTHORITY'}


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
    if manifest.get('compatibility_version') != CONTRACT_VERSION:
        fail('suite compatibility version is unsupported')
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
    if set(manifest.get('authority_boundary',{})) != HUMAN_GATES:
        fail('compatibility manifest must preserve exactly the three human gates')
    for gate, state in manifest.get("authority_boundary", {}).items():
        if state != "OPEN":
            fail(f"human gate {gate} must remain OPEN")
    return manifest


def validate_repo(repo: Path, validators: list[str], label: str) -> dict:
    if not (repo / ".git").exists():
        fail(f"{label} checkout missing .git: {repo}")
    git(repo, "rev-parse", "--verify", "HEAD")
    contract_path=repo/'PASV2-CONTRACT.json'
    if not contract_path.is_file():
        fail(f'{label} lacks its versioned component contract')
    contract=json.loads(contract_path.read_text(encoding='utf-8'))
    if git(repo,'show','HEAD:PASV2-CONTRACT.json') != contract_path.read_text(encoding='utf-8').strip():
        fail(f'{label} component contract has uncommitted changes')
    if contract.get('compatibility_version')!=CONTRACT_VERSION or contract.get('component')!=label:
        fail(f'{label} component/version is incompatible with this suite')
    if contract.get('authority_boundary')!={gate:'OPEN' for gate in HUMAN_GATES}:
        fail(f'{label} component authority boundaries changed')
    if not contract.get('interfaces'):
        fail(f'{label} has no executable interface bindings')
    for interface in contract['interfaces']:
        rel,symbol=interface.split('::',1)
        path=(repo/rel).resolve()
        if not path.is_relative_to(repo.resolve()) or not path.is_file():
            fail(f'{label} interface file does not resolve: {interface}')
        functions={node.name for node in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}
        if symbol not in functions:
            fail(f'{label} executable interface is absent: {interface}')
        if git(repo,'show','HEAD:'+rel) != path.read_text(encoding='utf-8').strip():
            fail(f'{label} interface differs from the reported commit: {interface}')
    for validator in validators:
        rel = validator.split()[0]
        if not (repo / rel).is_file():
            fail(f"{label} required validator missing: {rel}")
    return {'component':label,'compatibility_version':CONTRACT_VERSION,'head':git(repo,'rev-parse','HEAD'),'tree':git(repo,'rev-parse','HEAD^{tree}'),'interfaces':contract['interfaces']}


def validate_checkout_ref(repo: Path, expected: str, label: str) -> None:
    branch = git(repo, "branch", "--show-current")
    if not branch or branch == expected:
        return
    if branch != 'main':
        fail(f"{label} checkout branch drift: expected {expected} or integrated main, got {branch}")
    # A protected merge commit retains the audited branch's ancestry. Merely
    # naming a checkout main must not bypass the compatibility binding.
    for ref in ('refs/remotes/origin/' + expected, 'refs/heads/' + expected):
        exists = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--verify', ref], capture_output=True)
        if exists.returncode == 0:
            ancestor = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', ref, 'HEAD'], capture_output=True)
            if ancestor.returncode:
                fail(f'{label} main does not contain compatible reference {ref}')
            return
    fail(f'{label} integrated main requires a fetched compatible reference: {expected}')


def validate_local_checkouts(manifest: dict, blueprint: Path | None, preos: Path | None, gstack: Path | None, *, execute=False) -> list:
    repos = {"blueprint": blueprint, "preos": preos, "gstack": gstack}
    observed=[]
    for key, repo in repos.items():
        if repo is None:
            continue
        item = manifest["components"][key]
        observed.append(validate_repo(repo.resolve(), list(item["required_validators"]), key))
        if key in {"blueprint", "preos"}:
            validate_checkout_ref(repo.resolve(), item['ref'], key)
        if execute:
            for validator in item['required_validators']:
                if validator.startswith('scripts/validate-pasv2-compatibility.py'):
                    continue
                command=[sys.executable,*shlex.split(validator)]
                if validator.startswith('scripts/validate-three-repo-acceptance.py'):
                    if any(path is None for path in repos.values()):
                        fail('executing the cross-repository validator requires all three checkout paths')
                    for component,path in repos.items():
                        command.extend(['--'+component,str(path.resolve())])
                proc=subprocess.run(command,cwd=repo,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300)
                if proc.returncode:
                    fail(f'{key} actual validator failed: {validator}\n{proc.stdout}\n{proc.stderr}')
                observed[-1].setdefault('validator_runs',[]).append({'command':command,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
    return observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", type=Path)
    parser.add_argument("--preos", type=Path)
    parser.add_argument("--gstack", type=Path)
    parser.add_argument('--execute',action='store_true',help='Execute the manifest validators against these checkouts')
    args = parser.parse_args()
    manifest = validate_static()
    observed=validate_local_checkouts(manifest, args.blueprint, args.preos, args.gstack,execute=args.execute)
    print(json.dumps({'compatibility_version':CONTRACT_VERSION,'observed_checkouts':observed,'validator_execution_requested':args.execute},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
