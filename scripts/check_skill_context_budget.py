#!/usr/bin/env python3
"""Check gstack skill/router context budgets.

This repository already has large generated skills and section-carved skills.
The checker therefore measures every primary template/generated skill and section,
while failing only unapproved source routers and required-carve regressions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git", ".agents", ".factory", ".gbrain", ".hermes", ".openclaw",
    ".claude", ".codex", ".kiro", ".opencode", ".slate", "node_modules",
}


def line_count(text: str) -> int:
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def is_skipped(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in SKIP_DIRS for part in rel_parts)


def iter_candidates(root: Path) -> list[Path]:
    candidates: set[Path] = set()
    for pattern in ("*/SKILL.md", "*/SKILL.md.tmpl", "*/sections/*.md", "*/sections/*.md.tmpl"):
        for path in root.glob(pattern):
            if path.is_file() and not is_skipped(path, root):
                candidates.add(path)
    return sorted(candidates, key=lambda p: p.as_posix())


def classify(rel: str) -> str:
    if rel.endswith("/SKILL.md.tmpl"):
        return "source-router"
    if rel.endswith("/SKILL.md"):
        return "generated-skill"
    if "/sections/" in rel:
        return "section-template" if rel.endswith(".tmpl") else "section"
    return "other"


def require_carve(root: Path, policy: dict[str, Any], failures: list[str]) -> None:
    budgets = policy["budgets"]
    for skill, cfg in policy.get("required_carves", {}).items():
        template = root / cfg["template"]
        generated = root / cfg["generated"]
        manifest = root / cfg["manifest"]
        for path in (template, generated, manifest):
            if not path.is_file():
                failures.append(f"{skill}: required carve artifact missing: {path.relative_to(root).as_posix()}")
                continue
        if not (template.is_file() and generated.is_file() and manifest.is_file()):
            continue

        template_text = template.read_text(encoding="utf-8")
        generated_text = generated.read_text(encoding="utf-8")
        manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
        listed = [entry["file"] for entry in manifest_data.get("sections", [])]
        for section in cfg["sections"]:
            section_path = root / skill / "sections" / section
            source_path = root / skill / "sections" / f"{section}.tmpl"
            if section not in listed:
                failures.append(f"{skill}: manifest does not list sections/{section}")
            if not section_path.is_file():
                failures.append(f"{skill}: generated section missing: sections/{section}")
            if not source_path.is_file():
                failures.append(f"{skill}: section template missing: sections/{section}.tmpl")
            if f"sections/{section}" not in generated_text:
                failures.append(f"{skill}: generated skeleton does not route to sections/{section}")

        template_lines = line_count(template_text)
        if template_lines > cfg.get("source_template_max_lines", budgets["source_router_hard_review_lines"]):
            failures.append(f"{skill}: source template has {template_lines} lines")
        generated_lines = line_count(generated_text)
        if generated_lines > cfg.get("generated_skeleton_max_lines", budgets["generated_skill_hard_review_lines"]):
            failures.append(f"{skill}: generated skeleton has {generated_lines} lines")

        section_union = ""
        for section in cfg["sections"]:
            section_path = root / skill / "sections" / section
            if section_path.is_file():
                section_union += "\n" + section_path.read_text(encoding="utf-8")
        for marker in cfg.get("moved_markers", []):
            if marker in template_text:
                failures.append(f"{skill}: moved marker still in source skeleton: {marker}")
            if marker not in section_union:
                failures.append(f"{skill}: moved marker missing from section union: {marker}")
        for marker in cfg.get("skeleton_markers", []):
            if marker not in template_text and marker not in generated_text:
                failures.append(f"{skill}: skeleton marker missing: {marker}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Check gstack skill/router context budgets.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--policy", default=None)
    args = ap.parse_args()

    root = Path(args.repo).resolve()
    policy_path = Path(args.policy).resolve() if args.policy else root / "config" / "context-budget-policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    budgets = policy["budgets"]
    exceptions = set(policy.get("approved_exceptions", {}).keys())
    failures: list[str] = []
    warnings: list[str] = []
    rows: list[tuple[str, int, int, int, str, str]] = []

    for path in iter_candidates(root):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lines = line_count(text)
        size = len(text.encode("utf-8"))
        kind = classify(rel)
        status = "OK"

        if kind == "source-router":
            if lines > budgets["source_router_hard_review_lines"] and rel not in exceptions:
                status = "FAIL"
                failures.append(f"{rel}: source router {lines} lines exceeds hard review limit {budgets['source_router_hard_review_lines']}")
            elif lines > budgets["source_router_warning_lines"]:
                status = "EXEMPT" if rel in exceptions else "WARN"
                warnings.append(f"{rel}: source router {lines} lines exceeds warning limit {budgets['source_router_warning_lines']}")
            if text.count("{{PREAMBLE}}") > 1:
                status = "FAIL"
                failures.append(f"{rel}: duplicates {{PREAMBLE}} resolver")
        elif kind == "generated-skill":
            if lines > budgets["generated_skill_hard_review_lines"] and rel not in exceptions:
                status = "FAIL"
                failures.append(f"{rel}: generated skill {lines} lines exceeds hard review limit {budgets['generated_skill_hard_review_lines']}")
            elif lines > budgets["generated_skill_warning_lines"]:
                status = "WARN"
                warnings.append(f"{rel}: generated skill {lines} lines exceeds warning limit {budgets['generated_skill_warning_lines']}")
        elif kind in {"section", "section-template"}:
            if lines > budgets["section_hard_review_lines"]:
                status = "FAIL"
                failures.append(f"{rel}: section {lines} lines exceeds hard review limit {budgets['section_hard_review_lines']}")
            elif lines > budgets["section_warning_lines"]:
                status = "WARN"
                warnings.append(f"{rel}: section {lines} lines exceeds warning limit {budgets['section_warning_lines']}")

        rows.append((rel, lines, size, approx_tokens(text), kind, status))

    require_carve(root, policy, failures)

    print("path\tlines\tbytes\tapprox_tokens\tkind\tstatus")
    for row in rows:
        print("\t".join(map(str, row)))
    print(f"\nchecked={len(rows)} warnings={len(warnings)} failures={len(failures)}")
    if warnings:
        print("WARNINGS:")
        for item in warnings:
            print(f"- {item}")
    if failures:
        print("FAILURES:")
        for item in failures:
            print(f"- {item}")
        return 1
    print("PASS: skill context budgets and required carves are satisfied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
