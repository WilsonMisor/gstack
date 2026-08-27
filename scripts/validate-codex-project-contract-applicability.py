#!/usr/bin/env python3
"""Fail closed if non-Codex host checks are made release-blocking for this Project Contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "acceptance" / "codex-project-contract-ci-applicability.json"
EVALS = ROOT / ".github" / "workflows" / "evals.yml"

EXPECTED_STATES = ["APPLIES", "CONDITIONAL", "NOT_APPLICABLE", "ESCALATE", "FORBIDDEN"]
NON_CODEX_CREDENTIALS = {"ANTHROPIC_API_KEY", "Claude Code login", "GEMINI_API_KEY", "Gemini CLI login"}
REQUIRED_NON_CODEX_ROWS = {
    "e2e-pty-plan-smoke": "NOT_APPLICABLE",
    "e2e-gemini": "NOT_APPLICABLE",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    require(POLICY.is_file(), f"missing policy: {POLICY}")
    require(EVALS.is_file(), f"missing inherited eval workflow: {EVALS}")

    data = json.loads(POLICY.read_text(encoding="utf-8"))
    workflow = EVALS.read_text(encoding="utf-8")

    require(data.get("bounded_implementation_engine") == "OpenAI Codex",
            "bounded implementation engine must remain OpenAI Codex")
    require(data.get("gstack_role") == "multi-host specialist workforce",
            "gstack must remain a multi-host specialist workforce")
    require(data.get("gstack_multi_host_compatibility_preserved") is True,
            "gstack multi-host compatibility must remain preserved")
    require(data.get("non_codex_host_failures_block_this_project_contract") is False,
            "non-Codex host failures must not block this Codex Project Contract")
    require(data.get("applicability_states") == EXPECTED_STATES,
            "applicability vocabulary must match PREOS exactly")

    boundary = data.get("credential_boundary", {})
    forbidden_required = set(boundary.get("must_never_be_required_for_this_project_contract", []))
    require(NON_CODEX_CREDENTIALS.issubset(forbidden_required),
            "credential boundary must forbid Anthropic/Claude and Gemini credentials as Codex release prerequisites")

    checks = {item.get("id"): item for item in data.get("checks", []) if isinstance(item, dict)}
    require(checks.get("e2e-codex", {}).get("applicability") == "APPLIES",
            "authenticated Codex E2E must apply")
    require(checks.get("e2e-codex", {}).get("blocking") is True,
            "authenticated Codex E2E must be blocking")

    for check_id, expected in REQUIRED_NON_CODEX_ROWS.items():
        item = checks.get(check_id, {})
        require(item.get("applicability") == expected,
                f"{check_id} must be {expected} for this Project Contract")
        require(item.get("blocking") is False,
                f"{check_id} must not block this Project Contract")

    # Preserve inherited multi-host coverage: project-specific applicability must
    # never be implemented by deleting the upstream rows from gstack's eval suite.
    for token in ["e2e-codex", "e2e-pty-plan-smoke", "e2e-gemini"]:
        require(token in workflow, f"inherited eval workflow no longer preserves {token}")

    invariants = "\n".join(data.get("invariants", []))
    for token in [
        "Do not delete, weaken, skip globally, or fake-green",
        "Do not convert gstack into a Codex-only repository",
        "Do not request Anthropic, Gemini, or other non-Codex credentials",
        "Production authorization remains an accountable-human decision",
    ]:
        require(token in invariants, f"missing anti-regression invariant: {token}")

    print("PASS: Codex Project Contract applicability is fail-closed")
    print("PASS: Claude/Gemini host compatibility is preserved but non-blocking for this contract")
    print("PASS: non-Codex credentials cannot become Codex release prerequisites")


if __name__ == "__main__":
    main()
