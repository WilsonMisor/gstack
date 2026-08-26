#!/usr/bin/env python3
"""Deterministic executable specialist checks for disposable WordPress acceptance.

This is a repository-controlled, secretless execution surface for the four gstack
specialist roles used by the three-repository acceptance test. It does not claim
to replace an interactive/LLM specialist session. Instead, it executes the
machine-verifiable checks owned by each specialist contract and emits the actual
result as JSON evidence. Any failed check exits non-zero, so the caller cannot
manufacture a PASS label independently of execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

SPECIALISTS = {
    "review": ("review", "gstack-review"),
    "cso": ("cso", "gstack-cso"),
    "qa": ("qa", "gstack-qa"),
    "benchmark": ("benchmark", "gstack-benchmark"),
}


def fail(message: str) -> None:
    raise SystemExit(f"SPECIALIST_FAIL: {message}")


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        fail(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    return proc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_skill_contract(gstack: Path, specialist: str) -> tuple[Path, str]:
    skill_dir, producer = SPECIALISTS[specialist]
    skill = gstack / skill_dir / "SKILL.md"
    if not skill.is_file():
        fail(f"specialist contract missing: {skill}")
    text = skill.read_text(encoding="utf-8")
    if f"name: {skill_dir}" not in text:
        fail(f"specialist contract frontmatter does not identify {skill_dir}")
    return skill, producer


def php_files(repo: Path) -> list[Path]:
    return sorted(p for p in repo.rglob("*.php") if ".git" not in p.parts)


def lint_php(repo: Path) -> list[dict]:
    checks: list[dict] = []
    files = php_files(repo)
    if not files:
        fail("no PHP implementation files found")
    for path in files:
        rel = path.relative_to(repo).as_posix()
        proc = run(["php", "-l", str(path)], repo)
        checks.append({"check": "php-syntax", "target": rel, "status": "PASS", "output": proc.stdout.strip()})
    return checks


def runtime_check(repo: Path, runtime_test: Path) -> dict:
    proc = run(["php", str(runtime_test)], repo)
    if "PASS WordPress PHP runtime contract" not in proc.stdout:
        fail("PHP runtime contract did not emit its success marker")
    return {
        "check": "wordpress-php-runtime",
        "command": f"php {runtime_test.relative_to(repo).as_posix()}",
        "status": "PASS",
        "output": proc.stdout.strip(),
    }


def contract_check(repo: Path, contract_test: Path) -> dict:
    proc = run([sys.executable, str(contract_test)], repo)
    if "PASS classic WordPress theme + custom plugin contract" not in proc.stdout:
        fail("WordPress structural contract did not emit its success marker")
    return {
        "check": "wordpress-structural-contract",
        "command": f"{Path(sys.executable).name} {contract_test.relative_to(repo).as_posix()}",
        "status": "PASS",
        "output": proc.stdout.strip(),
    }


def review_checks(repo: Path, plugin: Path) -> tuple[list[dict], dict]:
    checks: list[dict] = []
    diff = run(["git", "diff", "--name-only", "HEAD^", "HEAD"], repo).stdout.splitlines()
    expected = plugin.relative_to(repo).as_posix()
    if diff != [expected]:
        fail(f"bounded implementation diff expanded outside custom plugin: {diff}")
    checks.append({"check": "bounded-diff", "status": "PASS", "changed_files": diff})

    theme = repo / "wp-content/themes/acme-classic"
    forbidden_paths = [theme / "theme.json", theme / "templates", theme / "parts"]
    existing = [p.relative_to(repo).as_posix() for p in forbidden_paths if p.exists()]
    if existing:
        fail(f"block/FSE artifacts present: {existing}")
    checks.append({"check": "classic-theme-boundary", "status": "PASS", "forbidden_paths_present": []})

    text = plugin.read_text(encoding="utf-8")
    forbidden_tokens = ["register_block_type(", "block.json", "wp-block-", "__return_true"]
    found = [token for token in forbidden_tokens if token in text]
    if found:
        fail(f"block/FSE implementation introduced: {found}")
    checks.append({"check": "no-block-implementation", "status": "PASS", "forbidden_tokens_present": []})
    return checks, {"changed_file_count": len(diff)}


def security_checks(repo: Path, plugin: Path, runtime_test: Path) -> tuple[list[dict], dict]:
    checks = lint_php(repo)
    text = plugin.read_text(encoding="utf-8")
    required = [
        "wp_nonce_field(", "wp_verify_nonce(", "current_user_can(",
        "sanitize_text_field(", "wp_unslash(", "update_post_meta(", "esc_attr(",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        fail(f"security controls missing from custom plugin: {missing}")
    checks.append({"check": "wordpress-security-controls", "status": "PASS", "required_tokens": required})
    checks.append(runtime_check(repo, runtime_test))
    return checks, {"security_controls_verified": len(required), "php_files_linted": len(php_files(repo))}


def qa_checks(repo: Path, contract_test: Path, runtime_test: Path) -> tuple[list[dict], dict]:
    checks = lint_php(repo)
    checks.append(contract_check(repo, contract_test))
    checks.append(runtime_check(repo, runtime_test))
    return checks, {"php_files_linted": len(php_files(repo)), "executable_contracts": 2}


def benchmark_checks(repo: Path, plugin: Path, runtime_test: Path) -> tuple[list[dict], dict]:
    checks: list[dict] = []
    durations: list[float] = []
    # This five-second ceiling is a CI harness health budget, not a product SLO.
    # It catches hangs/regressions in the disposable executable path while the
    # measured timings remain the performance evidence.
    for _ in range(3):
        start = time.perf_counter()
        runtime_check(repo, runtime_test)
        durations.append(time.perf_counter() - start)
    if max(durations) >= 5.0:
        fail(f"disposable WordPress runtime exceeded 5s harness budget: {durations}")
    checks.append({
        "check": "runtime-benchmark",
        "status": "PASS",
        "iterations": len(durations),
        "durations_seconds": [round(x, 6) for x in durations],
        "harness_budget_seconds": 5.0,
        "budget_kind": "CI_HARNESS_HEALTH_NOT_PRODUCT_SLO",
    })

    text = plugin.read_text(encoding="utf-8").lower()
    remote_markers = ["wp_remote_get(", "wp_remote_post(", "curl_exec(", "http://", "https://"]
    found = [marker for marker in remote_markers if marker in text]
    if found:
        fail(f"bounded plugin unexpectedly introduces remote-request dependency: {found}")
    checks.append({"check": "no-remote-request-dependency", "status": "PASS", "markers_present": []})
    total_php_bytes = sum(p.stat().st_size for p in php_files(repo))
    return checks, {
        "runtime_min_seconds": round(min(durations), 6),
        "runtime_max_seconds": round(max(durations), 6),
        "runtime_mean_seconds": round(sum(durations) / len(durations), 6),
        "php_bytes": total_php_bytes,
        "plugin_bytes": plugin.stat().st_size,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--specialist", choices=sorted(SPECIALISTS), required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--gstack", required=True)
    ap.add_argument("--plugin", required=True)
    ap.add_argument("--contract-test", required=True)
    ap.add_argument("--runtime-test", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    gstack = Path(args.gstack).resolve()
    plugin = Path(args.plugin).resolve()
    contract_test = Path(args.contract_test).resolve()
    runtime_test = Path(args.runtime_test).resolve()
    output = Path(args.output).resolve()
    skill, producer = require_skill_contract(gstack, args.specialist)

    if args.specialist == "review":
        checks, measurements = review_checks(repo, plugin)
    elif args.specialist == "cso":
        checks, measurements = security_checks(repo, plugin, runtime_test)
    elif args.specialist == "qa":
        checks, measurements = qa_checks(repo, contract_test, runtime_test)
    else:
        checks, measurements = benchmark_checks(repo, plugin, runtime_test)

    payload = {
        "schema_version": "1.0",
        "specialist": args.specialist,
        "producer": producer,
        "skill_contract": skill.relative_to(gstack).as_posix(),
        "skill_contract_sha256": sha256(skill),
        "execution_mode": "DETERMINISTIC_REPOSITORY_CONTROLLED_SPECIALIST_CHECK",
        "result": "PASS",
        "checks": checks,
        "measurements": measurements,
        "repo_head": run(["git", "rev-parse", "HEAD"], repo).stdout.strip(),
        "production_authority": "NOT_GRANTED_BY_SPECIALIST",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS {producer} executable specialist checks -> {output}")


if __name__ == "__main__":
    main()
