#!/usr/bin/env python3
"""Materialize and validate the source-based gstack Codex distribution."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_SKILLS = ROOT / ".agents" / "skills"
DIST = ROOT / "codex-distribution"
MANIFEST = ROOT / "CODEX-DISTRIBUTION.json"
BUILD_CONTRACT = ROOT / "CODEX-DISTRIBUTION-BUILD.json"
PROVENANCE = ".codex-distribution-provenance.json"
MATERIALIZER_VERSION = "source-runtime-materializer-v1"

RUNTIME_DIRS = ["bin", "lib", "browse/bin", "browse/dist", "design/dist", "make-pdf/dist", "browser-skills"]
RUNTIME_FILES = [
    "ETHOS.md", "VERSION", "scripts/jargon-list.json", "scripts/question-registry.ts",
    "supabase/config.sh", "review/checklist.md", "review/design-checklist.md",
    "review/greptile-triage.md", "review/TODOS-format.md",
]
SIDECAR_SKILL_REFS = ["gstack-upgrade", "office-hours", "plan-ceo-review", "plan-design-review", "plan-devex-review", "plan-eng-review"]
IGNORE_NAMES = {"__pycache__", ".pytest_cache", "node_modules", ".git", ".materializer"}
IGNORE_SUFFIXES = {".pyc", ".pyo", ".log", ".bun-build"}
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json", ".toml", ".txt"}

RUNTIME_ARTIFACTS = [
    ("gstack-global-discover", "compiled_executable", ["bin/gstack-global-discover", "bin/gstack-global-discover.exe"], "bun build --compile bin/gstack-global-discover.ts --outfile bin/gstack-global-discover"),
    ("browse-cli", "compiled_executable", ["browse/dist/browse", "browse/dist/browse.exe"], "bun build browse/src/cli.ts --target=bun, scrub checkout paths, then bun build --compile repo-local scrubbed bundle --outfile browse/dist/browse"),
    ("find-browse-cli", "compiled_executable", ["browse/dist/find-browse", "browse/dist/find-browse.exe"], "bun build --compile browse/src/find-browse.ts --outfile browse/dist/find-browse"),
    ("design-cli", "compiled_executable", ["design/dist/design", "design/dist/design.exe"], "bun build --compile design/src/cli.ts --outfile design/dist/design"),
    ("make-pdf-cli", "compiled_executable", ["make-pdf/dist/pdf", "make-pdf/dist/pdf.exe"], "bun build --compile make-pdf/src/cli.ts --outfile make-pdf/dist/pdf"),
    ("browse-node-server", "node_bundle", ["browse/dist/server-node.mjs"], "bun build browse/src/server.ts --target=node --outfile browse/dist/server-node.mjs"),
    ("browse-bun-polyfill", "runtime_polyfill", ["browse/dist/bun-polyfill.cjs"], "copy browse/src/bun-polyfill.cjs browse/dist/bun-polyfill.cjs"),
    ("browse-version", "source_commit_marker", ["browse/dist/.version"], "write git rev-parse HEAD"),
    ("design-version", "source_commit_marker", ["design/dist/.version"], "write git rev-parse HEAD"),
    ("make-pdf-version", "source_commit_marker", ["make-pdf/dist/.version"], "write git rev-parse HEAD"),
]
COMPILE_COMMANDS = [
    ["build", "--compile", "browse/src/find-browse.ts", "--outfile", "browse/dist/find-browse"],
    ["build", "--compile", "design/src/cli.ts", "--outfile", "design/dist/design"],
    ["build", "--compile", "make-pdf/src/cli.ts", "--outfile", "make-pdf/dist/pdf"],
    ["build", "--compile", "bin/gstack-global-discover.ts", "--outfile", "bin/gstack-global-discover"],
]
NODE_EXTERNALS = ["playwright", "playwright-core", "diff", "bun:sqlite", "@ngrok/ngrok"]

class DistributionError(RuntimeError):
    pass

def run(args: list[str], *, cwd: Path = ROOT, check: bool = True) -> str:
    proc = subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and proc.returncode != 0:
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        raise DistributionError(f"command failed with exit {proc.returncode}: {' '.join(args)}")
    return proc.stdout.strip()

def bun() -> str:
    configured = os.environ.get("BUN_CMD")
    if configured:
        return configured
    found = shutil.which("bun")
    if found:
        return found
    raise DistributionError("bun is required to materialize the gstack Codex distribution")

def bun_run(args: list[str]) -> str:
    return run([bun(), *args])

def git(*args: str, check: bool = True) -> str:
    return run(["git", *args], check=check)

def head() -> str:
    return git("rev-parse", "HEAD")

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def tree_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        h.update(len(rel).to_bytes(4, "big")); h.update(rel)
        h.update(len(data).to_bytes(8, "big")); h.update(data)
    return h.hexdigest()

def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))

def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

def frontmatter_name(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        raise DistributionError(f"SKILL.md lacks frontmatter: {skill_md}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise DistributionError(f"malformed frontmatter: {skill_md}")
    match = re.search(r"(?mi)^name\s*:\s*['\"]?([^'\"\r\n]+)", parts[1])
    if not match:
        raise DistributionError(f"frontmatter lacks name: {skill_md}")
    return match.group(1).strip()

def normalize_generated_text() -> None:
    for path in GENERATED_SKILLS.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        data = path.read_bytes()
        normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if normalized != data:
            path.write_bytes(normalized)

def run_generation() -> None:
    if GENERATED_SKILLS.exists():
        shutil.rmtree(GENERATED_SKILLS)
    bun_run(["run", "gen:skill-docs", "--host", "codex"])
    normalize_generated_text()

def build_browse_cli() -> None:
    dist = ROOT / "browse" / "dist"
    build_dir = dist / ".materializer"
    dist.mkdir(parents=True, exist_ok=True)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_dir / "browse-cli.bundle.mjs"
    scrubbed = build_dir / "browse-cli.scrubbed.mjs"
    bun_run(["build", "browse/src/cli.ts", "--target=bun", "--outfile", bundle.relative_to(ROOT).as_posix()])
    text = bundle.read_text(encoding="utf-8")
    text = re.sub(r'var __dirname = "[^"\r\n]*browse\\\\src"', 'var __dirname = "$bunfs"', text)
    scrubbed.write_text(text, encoding="utf-8")
    bun_run(["build", "--compile", scrubbed.relative_to(ROOT).as_posix(), "--outfile", "browse/dist/browse"])
    shutil.rmtree(build_dir)

def build_node_server() -> None:
    dist = ROOT / "browse" / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    args = ["build", "browse/src/server.ts", "--target=node", "--outfile", "browse/dist/server-node.mjs"]
    for external in NODE_EXTERNALS:
        args.extend(["--external", external])
    bun_run(args)
    outfile = dist / "server-node.mjs"
    text = outfile.read_text(encoding="utf-8")
    text = text.replace("import.meta.dir", "__browseNodeSrcDir")
    text = re.sub(r'var __dirname = "[^"\r\n]*browse\\\\src"', "var __dirname = __browseNodeSrcDir", text)
    text = text.replace('import { Database } from "bun:sqlite";', 'const Database = null; // bun:sqlite stubbed on Node')
    header = "".join([
        "// Windows Node.js compatibility (auto-generated)\n",
        'import { fileURLToPath as _ftp } from "node:url";\n',
        'import { dirname as _dn } from "node:path";\n',
        'const __browseNodeSrcDir = _dn(_dn(_ftp(import.meta.url))) + "/src";\n',
        '{ const _r = createRequire(import.meta.url); _r("./bun-polyfill.cjs"); }\n',
        "// end compatibility\n",
    ])
    lines = text.splitlines(keepends=True)
    outfile.write_text((lines[0] + header + "".join(lines[1:])) if lines else header, encoding="utf-8")
    shutil.copy2(ROOT / "browse" / "src" / "bun-polyfill.cjs", dist / "bun-polyfill.cjs")

def write_version_files() -> None:
    current = head()
    for rel in ["browse/dist/.version", "design/dist/.version", "make-pdf/dist/.version"]:
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(current + "\n", encoding="utf-8")

def mark_executable(path: Path) -> None:
    if os.name != "nt" and path.exists():
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
def locate_runtime(root: Path, artifact: tuple) -> Path:
    artifact_id, _kind, candidates, _procedure = artifact
    for candidate in candidates:
        path = root / candidate
        if path.is_file():
            return path
    raise DistributionError(f"missing runtime artifact {artifact_id}: {' or '.join(candidates)}")

def require_runtime(root: Path) -> None:
    for artifact in RUNTIME_ARTIFACTS:
        locate_runtime(root, artifact)

def materialize_runtime() -> None:
    for rel in ["browse/dist", "design/dist", "make-pdf/dist"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)
    run_generation()
    build_browse_cli()
    for args in COMPILE_COMMANDS:
        bun_run(args)
    build_node_server()
    write_version_files()
    for artifact in RUNTIME_ARTIFACTS:
        for candidate in artifact[2]:
            mark_executable(ROOT / candidate)
    require_runtime(ROOT)

def ignore_runtime(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORE_NAMES or any(name.endswith(suffix) for suffix in IGNORE_SUFFIXES)}

def copy_item(src: Path, dst: Path) -> None:
    if not src.exists():
        raise DistributionError(f"missing source artifact: {src.relative_to(ROOT).as_posix()}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=ignore_runtime)
    else:
        shutil.copy2(src, dst)

def generated_skill_sources() -> list[tuple[str, Path]]:
    if not GENERATED_SKILLS.is_dir():
        raise DistributionError("generated Codex skill directory is missing; run bun run gen:skill-docs --host codex")
    found: list[tuple[str, Path]] = []
    seen: set[str] = set()
    for directory in sorted(p for p in GENERATED_SKILLS.iterdir() if p.is_dir()):
        skill_md = directory / "SKILL.md"
        if not skill_md.is_file():
            continue
        name = frontmatter_name(skill_md)
        if name in seen:
            raise DistributionError(f"duplicate generated Codex skill name: {name}")
        seen.add(name)
        found.append((name, directory))
    if "gstack" not in seen:
        raise DistributionError("generated Codex root gstack skill is missing")
    return sorted(found, key=lambda item: item[0])

def manifest_from_sources(source_by_name: dict[str, Path]) -> dict:
    return {
        "schema_version": "1.0",
        "repository": "WilsonMisor/gstack",
        "component": "gstack-codex-skills",
        "skills": [
            {"name": name, "source_path": f"codex-distribution/skills/{name}", **({"implicit_invocation": True} if name == "gstack" else {})}
            for name in sorted(source_by_name)
        ],
        "agents": [],
    }

def manifest_text(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"

def runtime_records(target: Path) -> list[dict]:
    root = target / "skills" / "gstack"
    records = []
    for artifact_id, kind, _candidates, procedure in RUNTIME_ARTIFACTS:
        path = locate_runtime(root, (artifact_id, kind, _candidates, procedure))
        records.append({
            "id": artifact_id,
            "kind": kind,
            "path": path.relative_to(root).as_posix(),
            "sha256": file_hash(path),
            "size_bytes": path.stat().st_size,
            "procedure": procedure,
        })
    return records

def generated_file_count(target: Path) -> int:
    return sum(1 for p in target.rglob("*") if p.is_file() and not p.is_symlink())

def load_build_contract() -> dict:
    if not BUILD_CONTRACT.is_file():
        raise DistributionError("missing CODEX-DISTRIBUTION-BUILD.json")
    data = read_json(BUILD_CONTRACT)
    if data.get("schema_version") != "1.0" or data.get("repository") != "WilsonMisor/gstack":
        raise DistributionError("invalid CODEX-DISTRIBUTION-BUILD.json identity")
    if data.get("materializer", {}).get("version") != MATERIALIZER_VERSION:
        raise DistributionError("CODEX-DISTRIBUTION-BUILD.json materializer version mismatch")
    return data

def write_provenance(target: Path, data: dict) -> None:
    contract = load_build_contract()
    payload_tree_sha256 = tree_hash(target)
    provenance = {
        "schema_version": "1.0",
        "repository": "WilsonMisor/gstack",
        "component": "gstack-codex-skills",
        "source_commit": head(),
        "source_dirty_tracked_files": bool(git("status", "--porcelain", "--untracked-files=no")),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "distribution_manifest": {"path": "CODEX-DISTRIBUTION.json", "sha256": hashlib.sha256(manifest_text(data).encode("utf-8")).hexdigest()},
        "build_contract": {"path": "CODEX-DISTRIBUTION-BUILD.json", "sha256": file_hash(BUILD_CONTRACT)},
        "materializer": {
            "path": "scripts/build_codex_distribution.py",
            "version": MATERIALIZER_VERSION,
            "sha256": file_hash(Path(__file__).resolve()),
            "procedure": contract["materializer"]["procedure"],
            "check_procedure": contract["materializer"]["check_procedure"],
        },
        "compatibility": {
            "python": platform.python_version(),
            "bun": bun_run(["--version"]),
            "platform": platform.platform(),
            "gstack_package_version": str(read_json(ROOT / "package.json").get("version", "UNKNOWN")),
            "manifest_schema_version": data["schema_version"],
            "build_contract_version": contract["schema_version"],
        },
        "version_control_policy": contract["version_control_policy"],
        "generated_payload_tree_sha256": payload_tree_sha256,
        "generated_file_count_without_provenance": generated_file_count(target),
        "runtime_artifacts": runtime_records(target),
    }
    text = json.dumps(provenance, indent=2) + "\n"
    (target / PROVENANCE).write_text(text, encoding="utf-8")
    (target / "skills" / "gstack" / PROVENANCE).write_text(text, encoding="utf-8")

def validate_distribution(target: Path, data: dict) -> None:
    seen: set[str] = set()
    for item in data["skills"]:
        name = item["name"]
        if name in seen:
            raise DistributionError(f"duplicate skill name: {name}")
        seen.add(name)
        rel = Path(item["source_path"]).relative_to("codex-distribution")
        path = target / rel
        if not path.is_dir():
            raise DistributionError(f"declared skill source missing: {item['source_path']}")
        actual = frontmatter_name(path / "SKILL.md")
        if actual != name:
            raise DistributionError(f"skill name mismatch for {item['source_path']}: manifest={name}, SKILL.md={actual}")
    require_runtime(target / "skills" / "gstack")

def validate_provenance(target: Path) -> dict:
    path = target / PROVENANCE
    if not path.is_file():
        raise DistributionError(f"missing provenance file: {path}")
    data = read_json(path)
    if data.get("repository") != "WilsonMisor/gstack" or data.get("source_commit") != head():
        raise DistributionError("distribution provenance is not bound to the current gstack commit")
    by_id = {item["id"]: item for item in data.get("runtime_artifacts", [])}
    root = target / "skills" / "gstack"
    for artifact_id, _kind, _candidates, _procedure in RUNTIME_ARTIFACTS:
        item = by_id.get(artifact_id)
        if not item:
            raise DistributionError(f"provenance missing runtime artifact: {artifact_id}")
        installed = root / item["path"]
        if not installed.is_file() or file_hash(installed) != item["sha256"]:
            raise DistributionError(f"runtime artifact hash mismatch: {item.get('path')}")
    return data

def build_tree(target: Path, *, build_runtime: bool = True) -> dict:
    if build_runtime:
        materialize_runtime()
    else:
        run_generation(); require_runtime(ROOT)
    source_by_name = dict(generated_skill_sources())
    skills_out = target / "skills"
    for name, source_dir in sorted(source_by_name.items()):
        copy_item(source_dir, skills_out / name)
    sidecar = skills_out / "gstack"
    for rel in RUNTIME_DIRS:
        copy_item(ROOT / rel, sidecar / rel)
    for rel in RUNTIME_FILES:
        copy_item(ROOT / rel, sidecar / rel)
    for name in SIDECAR_SKILL_REFS:
        source_dir = source_by_name.get(name)
        if source_dir is None:
            raise DistributionError(f"sidecar skill reference is not generated: {name}")
        copy_item(source_dir / "SKILL.md", sidecar / name / "SKILL.md")
    data = manifest_from_sources(source_by_name)
    validate_distribution(target, data)
    write_provenance(target, data)
    validate_provenance(target)
    return data

def validate_manifest_file() -> None:
    run_generation()
    expected = manifest_text(manifest_from_sources(dict(generated_skill_sources())))
    if not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8-sig") != expected:
        raise DistributionError("CODEX-DISTRIBUTION.json is stale; run python scripts/build_codex_distribution.py")

def validate_current_distribution() -> None:
    validate_manifest_file(); load_build_contract()
    if not DIST.is_dir():
        raise DistributionError("codex-distribution is not materialized; run python scripts/build_codex_distribution.py")
    data = read_json(MANIFEST)
    validate_distribution(DIST, data)
    validate_provenance(DIST)

def publication_hygiene_errors() -> list[str]:
    errors = []
    tracked = git("ls-files", "codex-distribution").splitlines()
    if tracked:
        errors.append(f"codex-distribution must not be tracked; found {len(tracked)} tracked path(s)")
    ignored = subprocess.run(["git", "check-ignore", "-q", "codex-distribution/generated-probe"], cwd=ROOT).returncode == 0
    if not ignored:
        errors.append("codex-distribution/ is not ignored")
    lfs = git("lfs", "ls-files", check=False).splitlines()
    bad_lfs = [line for line in lfs if "codex-distribution/" in line]
    if bad_lfs:
        errors.append("codex-distribution has tracked LFS objects: " + ", ".join(bad_lfs[:5]))
    attrs = git("check-attr", "filter", "--", "codex-distribution/skills/gstack/browse/dist/browse.exe", check=False)
    if "filter: lfs" in attrs:
        errors.append("codex-distribution .exe files still resolve to Git LFS")
    return errors

def check_source_materialization() -> None:
    with tempfile.TemporaryDirectory(prefix="gstack-codex-distribution-") as td:
        data = build_tree(Path(td) / "codex-distribution")
        if not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8-sig") != manifest_text(data):
            raise DistributionError("CODEX-DISTRIBUTION.json is stale")
        errors = publication_hygiene_errors()
        if errors:
            raise DistributionError("; ".join(errors))
        print("gstack Codex distribution materializes from source")
        print(f"declared skills: {len(data['skills'])}")
        print(f"runtime artifacts: {len(RUNTIME_ARTIFACTS)}")
        print("publication hygiene: no tracked codex-distribution files or LFS objects")

def augment_receipt(receipt_path: Path) -> None:
    validate_current_distribution()
    receipt = read_json(receipt_path)
    provenance = validate_provenance(DIST)
    root_skill = next((i for i in receipt.get("skills", []) if i.get("repository") == "WilsonMisor/gstack" and i.get("name") == "gstack"), None)
    if not root_skill:
        raise DistributionError("receipt does not contain installed WilsonMisor/gstack root skill")
    dest = Path(root_skill["destination"])
    installed = []
    for item in provenance["runtime_artifacts"]:
        path = dest / item["path"]
        if not path.is_file():
            raise DistributionError(f"installed runtime artifact missing: {path}")
        installed_hash = file_hash(path)
        if installed_hash != item["sha256"]:
            raise DistributionError(f"installed runtime hash mismatch: {item['path']}")
        installed.append({"id": item["id"], "path": item["path"], "destination": str(path), "generated_sha256": item["sha256"], "installed_sha256": installed_hash, "size_bytes": path.stat().st_size})
    materialization = {
        "repository": "WilsonMisor/gstack",
        "source_commit": provenance["source_commit"],
        "distribution_build_procedure": provenance["materializer"],
        "build_contract": provenance["build_contract"],
        "generated_at_utc": provenance["generated_at_utc"],
        "receipt_augmented_at_utc": datetime.now(timezone.utc).isoformat(),
        "installation_destination": str(dest),
        "compatibility": provenance["compatibility"],
        "generated_distribution_tree_sha256": tree_hash(DIST),
        "installed_root_skill_tree_sha256": tree_hash(dest),
        "runtime_artifacts": provenance["runtime_artifacts"],
        "installed_runtime_artifacts": installed,
        "version_control_policy": provenance["version_control_policy"],
    }
    kept = [m for m in receipt.get("distribution_materializations", []) if m.get("repository") != "WilsonMisor/gstack"]
    receipt["distribution_materializations"] = kept + [materialization]
    receipt.setdefault("receipt_extensions", {})["gstack_source_runtime_materialization"] = MATERIALIZER_VERSION
    write_json(receipt_path, receipt)
    print(f"augmented receipt: {receipt_path}")
    print(f"installed runtime artifacts verified: {len(installed)}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="materialize in a temp tree and verify publication hygiene")
    parser.add_argument("--validate-current", action="store_true", help="validate the materialized local codex-distribution tree")
    parser.add_argument("--no-runtime-build", action="store_true", help="copy existing runtime outputs without rebuilding them")
    parser.add_argument("--augment-receipt", type=Path, help="augment an installation receipt with gstack materialization metadata")
    args = parser.parse_args()
    try:
        if args.augment_receipt:
            augment_receipt(args.augment_receipt); return 0
        if args.validate_current:
            validate_current_distribution(); print("gstack Codex distribution materialization is valid"); return 0
        if args.check:
            check_source_materialization(); return 0
        if DIST.exists():
            shutil.rmtree(DIST)
        data = build_tree(DIST, build_runtime=not args.no_runtime_build)
        MANIFEST.write_text(manifest_text(data), encoding="utf-8")
        print(f"wrote {MANIFEST.relative_to(ROOT)}")
        print(f"materialized {DIST.relative_to(ROOT)}")
        print(f"declared skills: {len(data['skills'])}")
        return 0
    except DistributionError as exc:
        print(f"gstack Codex distribution validation failed: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())