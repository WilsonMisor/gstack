#!/usr/bin/env python3
"""Disposable WordPress three-repository end-to-end acceptance.

This harness proves the current remediation contract using a real disposable Git
repository containing a classic WordPress theme plus custom plugin. It invokes
Blueprint source intake/semantic extraction, PREOS runtime/recovery/evidence/
hard-checkpoint/gate mechanics, and validates gstack specialist boundaries.

The bounded implementation edit is deterministic fixture code. This secretless
repository-controlled job MUST NOT claim that an authenticated external Codex
model ran. It also MUST NOT deploy anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
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


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(cmd: list[str], *, cwd: Path, env: dict[str, str] | None = None,
        check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd, cwd=cwd, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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


def recursive_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()


def create_wordpress_fixture(app: Path) -> dict[str, Path]:
    requirements = app / "docs" / "requirements.md"
    architecture = app / "docs" / "architecture.md"
    style = app / "wp-content" / "themes" / "acme-classic" / "style.css"
    functions = app / "wp-content" / "themes" / "acme-classic" / "functions.php"
    header = app / "wp-content" / "themes" / "acme-classic" / "header.php"
    footer = app / "wp-content" / "themes" / "acme-classic" / "footer.php"
    index = app / "wp-content" / "themes" / "acme-classic" / "index.php"
    plugin = app / "wp-content" / "plugins" / "acme-core" / "acme-core.php"
    tests = app / "tests" / "test_wordpress_contract.py"
    config = app / "config" / "wordpress-test.json"
    schema = app / "config" / "content-schema.json"
    deps = app / "composer.json"

    write(requirements, """# WordPress Product Requirements

## Requirements

- The website must use a code-only classic WordPress theme and a custom-made plugin.
- Gutenberg, Full Site Editing, block themes, and the block editor must remain disabled.
- The custom plugin must register a `property` custom post type without routing editors into the block editor.
- Property editing must use a classic meta box with nonce verification, capability checks, sanitization, and escaped output.
- The theme must provide classic PHP templates and must not depend on `theme.json` or block template directories.
- Production release must remain blocked until an accountable human grants production authorization.
- Security, review, QA, and performance evidence must be independent, current, and bound to the governed implementation.
""")
    write(architecture, """# Declared Architecture

The approved delivery architecture is WordPress using a code-only classic PHP theme plus a custom PHP plugin.
The frontend is server-rendered by classic WordPress PHP templates. The plugin owns the `property` custom post type and classic meta fields.
Gutenberg, Full Site Editing, block themes, and block-based editing are forbidden for this profile.
The technology stack uses WordPress, PHP, HTML, CSS, and MySQL-compatible WordPress persistence.
""")
    write(style, """/*
Theme Name: ACME Classic
Description: Disposable classic-theme acceptance fixture.
Version: 1.0.0
*/
body { font-family: sans-serif; }
""")
    write(functions, """<?php
if (!defined('ABSPATH')) { exit; }

add_theme_support('title-tag');
add_theme_support('post-thumbnails');
add_filter('use_block_editor_for_post', '__return_false', 100);
add_filter('use_block_editor_for_post_type', '__return_false', 100);
add_filter('gutenberg_can_edit_post_type', '__return_false', 100);
""")
    write(header, """<!doctype html>
<html <?php language_attributes(); ?>>
<head><meta charset="<?php bloginfo('charset'); ?>"><?php wp_head(); ?></head>
<body <?php body_class(); ?>>
<header><a href="<?php echo esc_url(home_url('/')); ?>"><?php bloginfo('name'); ?></a></header>
<main>
""")
    write(footer, """</main>
<footer><?php echo esc_html(get_bloginfo('name')); ?></footer>
<?php wp_footer(); ?></body></html>
""")
    write(index, """<?php get_header(); ?>
<?php while (have_posts()) : the_post(); ?>
<article><h1><?php the_title(); ?></h1><?php the_content(); ?></article>
<?php endwhile; ?>
<?php get_footer(); ?>
""")

    # Baseline plugin intentionally lacks the governed property implementation.
    # The deterministic bounded edit below supplies it, without claiming that an
    # authenticated Codex model executed in this secretless CI job.
    write(plugin, """<?php
/**
 * Plugin Name: ACME Core
 * Description: Disposable custom-code plugin acceptance fixture.
 * Version: 1.0.0
 */
if (!defined('ABSPATH')) { exit; }
""")

    write(tests, r'''from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wp-content/themes/acme-classic"
PLUGIN = ROOT / "wp-content/plugins/acme-core/acme-core.php"

required_theme = ["style.css", "functions.php", "header.php", "footer.php", "index.php"]
missing = [name for name in required_theme if not (THEME / name).is_file()]
if missing:
    raise SystemExit("missing classic theme files: " + ", ".join(missing))

for forbidden in [THEME / "theme.json", THEME / "templates", THEME / "parts"]:
    if forbidden.exists():
        raise SystemExit(f"block/FSE artifact forbidden in classic fixture: {forbidden}")

functions = (THEME / "functions.php").read_text(encoding="utf-8")
for token in ["use_block_editor_for_post", "use_block_editor_for_post_type", "gutenberg_can_edit_post_type"]:
    if token not in functions or "__return_false" not in functions:
        raise SystemExit(f"block editor disablement missing: {token}")

plugin = PLUGIN.read_text(encoding="utf-8")
required_plugin = [
    "register_post_type('property'", "'show_in_rest' => false", "add_meta_box(",
    "wp_nonce_field(", "wp_verify_nonce(", "current_user_can(",
    "sanitize_text_field(", "update_post_meta(", "esc_attr(",
]
for token in required_plugin:
    if token not in plugin:
        raise SystemExit(f"custom plugin contract missing: {token}")

for forbidden in ["register_block_type(", "block.json", "wp-block-", "use_block_editor_for_post_type', '__return_true"]:
    if forbidden in plugin:
        raise SystemExit(f"forbidden block implementation detected: {forbidden}")

print("PASS classic WordPress theme + custom plugin contract")
''')
    write(config, json.dumps({
        "profile": "wordpress-classic-custom-plugin",
        "block_editor": False,
        "full_site_editing": False,
        "deployment": "forbidden-in-disposable-e2e",
    }, indent=2) + "\n")
    write(schema, json.dumps({
        "custom_post_type": "property",
        "meta_fields": ["_acme_property_reference"],
        "editor": "classic-meta-box",
    }, indent=2) + "\n")
    write(deps, json.dumps({
        "name": "acme/disposable-wordpress-fixture",
        "type": "project",
        "require": {"php": ">=8.1"},
    }, indent=2) + "\n")

    return {
        "requirements": requirements,
        "architecture": architecture,
        "style": style,
        "functions": functions,
        "plugin": plugin,
        "tests": tests,
        "config": config,
        "schema": schema,
        "deps": deps,
    }


def bounded_codex_fixture_edit(plugin: Path) -> None:
    write(plugin, """<?php
/**
 * Plugin Name: ACME Core
 * Description: Disposable custom-code plugin acceptance fixture.
 * Version: 1.1.0
 */
if (!defined('ABSPATH')) { exit; }

function acme_register_property_cpt() {
    register_post_type('property', [
        'label' => 'Properties',
        'public' => true,
        'show_in_rest' => false,
        'supports' => ['title', 'editor', 'thumbnail'],
    ]);
}
add_action('init', 'acme_register_property_cpt');

function acme_property_meta_box() {
    add_meta_box('acme-property-reference', 'Property Reference', 'acme_property_meta_box_render', 'property', 'normal', 'default');
}
add_action('add_meta_boxes_property', 'acme_property_meta_box');

function acme_property_meta_box_render($post) {
    wp_nonce_field('acme_save_property_reference', 'acme_property_reference_nonce');
    $value = get_post_meta($post->ID, '_acme_property_reference', true);
    echo '<label for="acme_property_reference">Reference</label>';
    echo '<input id="acme_property_reference" name="acme_property_reference" value="' . esc_attr($value) . '">';
}

function acme_save_property_reference($post_id) {
    if (!isset($_POST['acme_property_reference_nonce'])) { return; }
    if (!wp_verify_nonce($_POST['acme_property_reference_nonce'], 'acme_save_property_reference')) { return; }
    if (!current_user_can('edit_post', $post_id)) { return; }
    if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) { return; }
    $value = isset($_POST['acme_property_reference'])
        ? sanitize_text_field(wp_unslash($_POST['acme_property_reference']))
        : '';
    update_post_meta($post_id, '_acme_property_reference', $value);
}
add_action('save_post_property', 'acme_save_property_reference');
""")


def assert_wordpress_overlay(preos: Path) -> None:
    overlay = read(preos / "references" / "wordpress" / "wordpress-75-control-overlay.md")
    ids = re.findall(r"\| (FS-\d{3}) \|", overlay)
    expected = [f"FS-{n:03d}" for n in range(1, 76)]
    require(ids == expected and len(set(ids)) == 75,
            "PREOS WordPress overlay is not exact FS-001..FS-075")
    print("PASS: PREOS WordPress overlay maps FS-001..FS-075 exactly once")


def assert_gstack_specialists(gstack: Path) -> None:
    integration = read(gstack / "PREOS-INTEGRATION.md")
    required = {
        "gstack-review": gstack / "review" / "SKILL.md",
        "gstack-cso": gstack / "cso" / "SKILL.md",
        "gstack-qa": gstack / "qa" / "SKILL.md",
        "gstack-benchmark": gstack / "benchmark" / "SKILL.md",
    }
    for route, skill in required.items():
        require(route in integration, f"gstack integration missing specialist route {route}")
        require(skill.is_file(), f"gstack specialist skill missing: {skill}")
    release = integration.partition("## Release relationship")[2]
    require("accountable human production approval" in release,
            "gstack release relationship lost human production approval boundary")
    require(release.find("accountable human production approval") < release.find("gstack-ship"),
            "gstack ship route appears before human production approval")
    print("PASS: gstack review/security/QA/performance specialists remain distinct and human-gated")


def wordpress_e2e(blueprint: Path, preos: Path, gstack: Path) -> None:
    source_intake = blueprint / "scripts" / "source_intake.py"
    preos_scripts = preos / "scripts"
    for required in [
        source_intake,
        preos_scripts / "init-project-state.py",
        preos_scripts / "checkpoint-state.py",
        preos_scripts / "recover-state.py",
        preos_scripts / "capture-evidence.py",
        preos_scripts / "validate-evidence.py",
        preos_scripts / "evaluate-gates.py",
        preos_scripts / "record-approval.py",
    ]:
        require(required.is_file(), f"required executable contract missing: {required}")

    with tempfile.TemporaryDirectory(prefix="three-repo-wordpress-e2e-") as td:
        base = Path(td)
        app = base / "wordpress-app"
        app.mkdir()
        paths = create_wordpress_fixture(app)

        decisions = base / "source-decisions.json"
        decisions.write_text(json.dumps({
            "project_mode": "BROWNFIELD",
            "source_decisions": [
                {"path": "docs/requirements.md", "authority": "HUMAN_APPROVED", "status": "CURRENT"},
                {"path": "docs/architecture.md", "authority": "HUMAN_APPROVED", "status": "CURRENT"},
                {"path": "wp-content/themes/acme-classic/functions.php", "authority": "IMPLEMENTATION_EVIDENCE", "status": "CURRENT"},
                {"path": "wp-content/plugins/acme-core/acme-core.php", "authority": "IMPLEMENTATION_EVIDENCE", "status": "CURRENT"}
            ],
            "approved_architecture": {
                "cms": "WordPress", "theme_model": "classic PHP theme",
                "extension_model": "custom-code plugin", "block_editor": "disabled",
                "full_site_editing": "disabled"
            },
            "approved_stack": {
                "cms": "WordPress", "language": "PHP",
                "theme": "classic", "plugin": "custom-code"
            },
            "unknowns": [], "assumptions": [], "role_gaps": [],
            "human_decisions_required": []
        }, indent=2) + "\n", encoding="utf-8")

        intake_proc = run([
            sys.executable, str(source_intake), str(app),
            "--project-root", str(app), "--decisions", str(decisions),
            "--intent", "disposable WordPress classic-theme custom-plugin three-repository acceptance",
        ], cwd=blueprint)
        intake = json.loads(read(app / ".ai-product-delivery" / "source-intake" / "SOURCE-INTAKE.json"))
        require(intake_proc.returncode == 0, "Blueprint WordPress intake did not complete")
        require(intake.get("project_mode") == "BROWNFIELD", "WordPress code was not classified BROWNFIELD")
        requirements = intake.get("source_requirements", [])
        require(len(requirements) >= 7, "automatic requirement extraction missed WordPress governed requirements")
        require(any(r.get("extraction_method") == "DETERMINISTIC_TEXT_CANDIDATE" for r in requirements),
                "WordPress requirements were not automatically extracted")
        require(all(r.get("requires_governed_review") for r in requirements if r.get("extraction_method") == "DETERMINISTIC_TEXT_CANDIDATE"),
                "automatic requirements bypassed governed review")
        observed_stack = recursive_text(intake.get("observed_stack", {}))
        require("wordpress" in observed_stack and "php" in observed_stack,
                "Blueprint did not observe WordPress + PHP from the disposable repository")
        declared_arch = recursive_text(intake.get("declared_architecture", {}))
        require("wordpress" in declared_arch and "classic" in declared_arch,
                "Blueprint did not extract declared classic WordPress architecture")
        semantic = intake.get("semantic_extraction", {})
        require(semantic.get("automatic_approval") is False,
                "automatic extraction incorrectly crossed the approval boundary")
        require(intake.get("approved_architecture", {}).get("theme_model") == "classic PHP theme",
                "governed approved architecture was not preserved separately")
        print("PASS: Blueprint automatically extracts WordPress requirements/architecture/stack without automatic approval")

        contract_dir = app / ".ai-product-delivery" / "project-contract"
        packet_dir = app / ".ai-product-delivery" / "task-packets"
        contract_dir.mkdir(parents=True, exist_ok=True)
        packet_dir.mkdir(parents=True, exist_ok=True)
        contract = contract_dir / "PROJECT-CONTRACT.json"
        contract.write_text(json.dumps({
            "project_id": "three-repo-wordpress",
            "project_contract_version": "PC-WP-1",
            "source_hashes": [
                {"artifact": "docs/requirements.md", "sha256": sha256(paths["requirements"])},
                {"artifact": "docs/architecture.md", "sha256": sha256(paths["architecture"])},
            ],
            "classification": {
                "profiles": ["wordpress", "classic-theme", "custom-plugin"],
                "production_assurance": "standard"
            },
            "authority": {"production_release": "Accountable Product Owner"}
        }, indent=2) + "\n", encoding="utf-8")
        packet = packet_dir / "TP-WP-001.md"
        packet.write_text("""# TP-WP-001

## Scope

Implement the `property` custom post type and classic meta-field workflow only in `wp-content/plugins/acme-core/acme-core.php`. Do not introduce Gutenberg, block themes, Full Site Editing, page builders, or block-based custom post editing.

## Required checks

- `python tests/test_wordpress_contract.py` must pass.
- The classic theme must contain PHP templates and no `theme.json`, `templates/`, or `parts/` block-theme artifacts.
- The custom plugin must use nonce verification, capability checks, sanitization, and escaped output.

## Required evidence

- Independent review evidence from gstack-review.
- Independent security evidence from gstack-cso.
- Independent QA evidence from gstack-qa.
- Independent performance evidence from gstack-benchmark.

## Authority

Deployment and production authorization remain human-only. This packet does not authorize release.
""", encoding="utf-8")

        git(app, "init")
        git(app, "config", "user.email", "wordpress-e2e@example.invalid")
        git(app, "config", "user.name", "WordPress E2E")
        git(app, "add", ".")
        git(app, "commit", "-m", "governed WordPress disposable baseline")

        env = os.environ.copy()
        env["PREOS_STATE_ROOT"] = str(base / "preos-state")
        env["WP_ENVIRONMENT_TYPE"] = "test"
        run([sys.executable, str(preos_scripts / "init-project-state.py"),
             "three-repo-wordpress", "--repo", str(app)], cwd=preos, env=env)

        bounded_codex_fixture_edit(paths["plugin"])
        soft = run([
            sys.executable, str(preos_scripts / "checkpoint-state.py"),
            "three-repo-wordpress", "--repo", str(app), "--kind", "soft",
            "--event", "SESSION_INTERRUPTED", "--project-contract", str(contract),
            "--project-contract-version", "PC-WP-1", "--task-packet", str(packet),
            "--task-packet-id", "TP-WP-001",
            "--last-verified-action", "bounded custom-plugin edit durably captured",
            "--next-unverified-action", "WordPress contract test",
            "--pending-test", "wordpress:classic-custom-plugin-contract",
            "--active-control-id", "FS-001", "--active-control-id", "FS-075",
        ], cwd=preos, env=env)
        require("SOFT CHECKPOINT" in soft.stdout, "PREOS did not persist interruption checkpoint")

        recovered = run([
            sys.executable, str(preos_scripts / "recover-state.py"),
            "three-repo-wordpress", "--repo", str(app),
        ], cwd=preos, env=env)
        recovery = json.loads(recovered.stdout)
        require(recovery.get("status") == "SAFE_TO_RESUME",
                "WordPress interrupted implementation did not recover SAFE_TO_RESUME")
        require(recovery.get("next_unverified_action") == "re-run uncertain test: wordpress:classic-custom-plugin-contract",
                "PREOS did not resume from the first unverified WordPress test")
        print("PASS: PREOS interruption recovery resumes the WordPress task at its first unverified action")

        wp_test = run([sys.executable, str(paths["tests"])], cwd=app)
        require("PASS classic WordPress theme + custom plugin contract" in wp_test.stdout,
                "disposable WordPress contract test did not pass")
        git(app, "add", "wp-content/plugins/acme-core/acme-core.php")
        git(app, "commit", "-m", "implement bounded classic WordPress custom plugin")
        require(git(app, "status", "--porcelain") == "", "implementation repository must be clean before evidence")

        artifact_dir = base / "specialist-evidence"
        artifact_dir.mkdir()
        specialists = {
            "E-WP-REVIEW": ("gstack-review", "Independent review PASS: bounded plugin scope; no block/FSE expansion."),
            "E-WP-SECURITY": ("gstack-cso", "Security PASS: nonce, capability check, sanitization, output escaping verified."),
            "E-WP-QA": ("gstack-qa", "QA PASS: classic-theme/custom-plugin contract test passed."),
            "E-WP-PERFORMANCE": ("gstack-benchmark", "Performance PASS: fixture introduces no remote request, queue, or render-loop dependency."),
        }
        evidence_paths: list[Path] = []
        for evidence_id, (producer, text) in specialists.items():
            artifact = artifact_dir / f"{evidence_id}.txt"
            artifact.write_text(text + "\n", encoding="utf-8")
            run([
                sys.executable, str(preos_scripts / "capture-evidence.py"),
                "three-repo-wordpress", evidence_id, "--repo", str(app),
                "--producer", producer, "--environment", "disposable-wordpress-e2e",
                "--artifact", str(artifact), "--project-contract", str(contract),
                "--task-packet", str(packet), "--source", str(paths["requirements"]),
                "--source", str(paths["architecture"]), "--config", str(paths["config"]),
                "--schema", str(paths["schema"]), "--dependency", str(paths["deps"]),
                "--test-definition", str(paths["tests"]), "--env-var", "WP_ENVIRONMENT_TYPE",
                "--test-or-command", "python tests/test_wordpress_contract.py",
                "--result", "PASS", "--requirement-id", "SRCREQ-WORDPRESS-E2E",
            ], cwd=preos, env=env)
            evidence_paths.append(
                Path(env["PREOS_STATE_ROOT"]) / "projects" / "three-repo-wordpress" /
                "production" / "evidence-records" / f"{evidence_id}.json"
            )

        strict = run([
            sys.executable, str(preos_scripts / "validate-evidence.py"),
            *map(str, evidence_paths), "--require-complete-bindings",
        ], cwd=preos, env=env)
        require("complete freshness bindings" in strict.stdout,
                "WordPress specialist evidence did not pass strict freshness validation")
        print("PASS: four independent WordPress specialist records are commit/source/contract/task/config/schema/dependency/test/environment bound")

        verification = base / "hard-verification.json"
        verification.write_text(json.dumps({
            "schema_version": "1.0",
            "checks": [
                {
                    "id": "wordpress-contract",
                    "status": "PASS",
                    "command_or_test": "python tests/test_wordpress_contract.py",
                    "evidence_id": "E-WP-QA"
                },
                {
                    "id": "security-review",
                    "status": "PASS",
                    "command_or_test": "gstack-cso governed specialist review",
                    "evidence_id": "E-WP-SECURITY"
                },
                {
                    "id": "code-review",
                    "status": "PASS",
                    "command_or_test": "gstack-review governed specialist review",
                    "evidence_id": "E-WP-REVIEW"
                },
                {
                    "id": "performance-review",
                    "status": "PASS",
                    "command_or_test": "gstack-benchmark governed specialist review",
                    "evidence_id": "E-WP-PERFORMANCE"
                }
            ],
            "evidence_ids": sorted(specialists),
            "traceability": "UPDATED",
            "rollback_point": git(app, "rev-parse", "HEAD")
        }, indent=2) + "\n", encoding="utf-8")

        hard = run([
            sys.executable, str(preos_scripts / "checkpoint-state.py"),
            "three-repo-wordpress", "--repo", str(app), "--kind", "hard",
            "--event", "IMPLEMENTATION_COMPLETE", "--project-contract", str(contract),
            "--project-contract-version", "PC-WP-1", "--task-packet", str(packet),
            "--task-packet-id", "TP-WP-001",
            "--last-verified-action", "WordPress contract and independent specialist evidence verified",
            "--next-unverified-action", "PREOS G0-G11 assurance",
            "--verification-manifest", str(verification),
            "--active-control-id", "FS-001", "--active-control-id", "FS-075",
        ], cwd=preos, env=env)
        require("HARD CHECKPOINT" in hard.stdout,
                "PREOS refused machine-verified WordPress hard checkpoint")
        print("PASS: PREOS hard checkpoint is clean-Git and machine-verification bound")

        gate_evidence = {
            "G0": ["E-WP-REVIEW"], "G1": ["E-WP-REVIEW"],
            "G2": ["E-WP-REVIEW"], "G3": ["E-WP-SECURITY"],
            "G4": ["E-WP-QA"], "G5": ["E-WP-REVIEW"],
            "G6": ["E-WP-PERFORMANCE"], "G7": ["E-WP-QA"],
            "G8": ["E-WP-QA"], "G9": ["E-WP-QA"],
            "G10": ["E-WP-SECURITY"],
            "G11": sorted(specialists),
        }
        gates_in = base / "wordpress-gates.json"
        gates_out = base / "wordpress-gates-out.json"
        gates_in.write_text(json.dumps({
            "gates": {
                gid: [{
                    "state": "GREEN", "evidence_ids": gate_evidence[gid],
                    "source": "disposable-wordpress-three-repo-e2e"
                }]
                for gid in [f"G{i}" for i in range(12)]
            }
        }, indent=2) + "\n", encoding="utf-8")
        run([
            sys.executable, str(preos_scripts / "evaluate-gates.py"),
            str(gates_in), "--output", str(gates_out),
        ], cwd=preos, env=env)
        gate_results = json.loads(read(gates_out))["gate_results"]
        expected_gates = [f"G{i}" for i in range(12)]
        require(list(gate_results) == expected_gates, "PREOS gate output is not exact G0-G11")
        require(all(gate_results[g]["state"] == "GREEN" for g in expected_gates),
                "strictly evidenced disposable WordPress gate chain did not evaluate GREEN")
        print("PASS: strict specialist evidence flows through exact PREOS G0-G11 gate mechanics")

        run([
            sys.executable, str(preos_scripts / "record-approval.py"),
            "three-repo-wordpress", "A-PROD", "--status", "PENDING",
            "--scope", "production authorization", "--authority", "Accountable Product Owner",
        ], cwd=preos, env=env)
        run([
            sys.executable, str(preos_scripts / "checkpoint-state.py"),
            "three-repo-wordpress", "--repo", str(app), "--kind", "soft",
            "--event", "APPROVAL_REQUIRED", "--project-contract", str(contract),
            "--project-contract-version", "PC-WP-1", "--task-packet", str(packet),
            "--task-packet-id", "TP-WP-001", "--required-approval", "A-PROD",
            "--last-verified-action", "G0-G11 assurance complete",
            "--next-unverified-action", "accountable human production authorization",
            "--release-status", "NOT_AUTHORIZED",
        ], cwd=preos, env=env)
        blocked = run([
            sys.executable, str(preos_scripts / "recover-state.py"),
            "three-repo-wordpress", "--repo", str(app),
        ], cwd=preos, env=env, check=False)
        require(blocked.returncode == 3, "pending production approval did not block WordPress recovery")
        blocked_state = json.loads(blocked.stdout)
        require(blocked_state.get("status") == "BLOCKED",
                "WordPress lifecycle did not remain BLOCKED before human production authorization")
        require(blocked_state.get("pending_approvals") == ["A-PROD"],
                "human production approval identity was not preserved")
        require(git(app, "status", "--porcelain") == "",
                "disposable E2E unexpectedly modified application repository after verified commit")
        print("PASS: production remains BLOCKED pending accountable human authorization; no deployment executed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True, type=Path)
    parser.add_argument("--preos", required=True, type=Path)
    parser.add_argument("--gstack", required=True, type=Path)
    args = parser.parse_args()
    blueprint = args.blueprint.resolve()
    preos = args.preos.resolve()
    gstack = args.gstack.resolve()
    assert_wordpress_overlay(preos)
    assert_gstack_specialists(gstack)
    wordpress_e2e(blueprint, preos, gstack)
    print("PASS: disposable WordPress Blueprint -> PREOS -> gstack/Codex-boundary E2E complete")


if __name__ == "__main__":
    main()
