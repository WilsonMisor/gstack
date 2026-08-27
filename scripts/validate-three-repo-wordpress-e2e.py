#!/usr/bin/env python3
"""Disposable WordPress three-repository end-to-end acceptance.

This harness proves the remediation contract using a real disposable Git
repository containing a code-only classic WordPress theme plus custom plugin.
It invokes Blueprint source intake/semantic extraction, derives the PREOS
Project Contract and AI Task Packet from that governed Blueprint output, uses
PREOS runtime/recovery/evidence/hard-checkpoint/gate mechanics, and executes
four distinct gstack-owned deterministic specialist checks before evidence is
recorded.

The bounded implementation edit is deterministic fixture code. This secretless
repository-controlled job MUST NOT claim that an authenticated external Codex
model ran. It MUST NOT authorize production or deploy anything.
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
    runtime_test = app / "tests" / "wordpress_runtime_contract.php"
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

    # Execute the real PHP theme/plugin inside a minimal WordPress-API stub. This
    # is not a fake WordPress implementation: the product PHP itself is loaded
    # and its hooks, CPT configuration, rendered escaped field, nonce path,
    # capability gate and sanitized update path are exercised. The stubs supply
    # only the WordPress functions needed by this disposable unit/runtime test.
    write(runtime_test, r'''<?php
declare(strict_types=1);
define('ABSPATH', __DIR__ . '/../');
$GLOBALS['wp_actions'] = [];
$GLOBALS['wp_filters'] = [];
$GLOBALS['wp_post_types'] = [];
$GLOBALS['wp_meta_boxes'] = [];
$GLOBALS['wp_updates'] = [];
$GLOBALS['can_edit'] = true;

function assertion(bool $condition, string $message): void {
    if (!$condition) { fwrite(STDERR, "RUNTIME_FAIL: $message\n"); exit(1); }
}
function add_theme_support($feature): void { $GLOBALS['theme_support'][] = $feature; }
function add_filter($hook, $callback, $priority = 10, $accepted_args = 1): void { $GLOBALS['wp_filters'][$hook][] = [$callback, $priority]; }
function add_action($hook, $callback, $priority = 10, $accepted_args = 1): void { $GLOBALS['wp_actions'][$hook][] = [$callback, $priority]; }
function register_post_type($type, $args): void { $GLOBALS['wp_post_types'][$type] = $args; }
function add_meta_box($id, $title, $callback, $screen, $context = 'advanced', $priority = 'default'): void { $GLOBALS['wp_meta_boxes'][$id] = compact('title', 'callback', 'screen', 'context', 'priority'); }
function wp_nonce_field($action, $name): void { $GLOBALS['nonce_fields'][$name] = $action; }
function get_post_meta($post_id, $key, $single = false) { return 'A&B"'; }
function esc_attr($value): string { return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function current_user_can($capability, $post_id = null): bool { return (bool)$GLOBALS['can_edit']; }
function wp_verify_nonce($nonce, $action): bool { return $nonce === 'nonce-ok' && $action === 'acme_save_property_reference'; }
function sanitize_text_field($value): string { return trim(strip_tags((string)$value)); }
function wp_unslash($value): string { return stripslashes((string)$value); }
function update_post_meta($post_id, $key, $value): void { $GLOBALS['wp_updates'][$post_id][$key] = $value; }

require ABSPATH . 'wp-content/themes/acme-classic/functions.php';
require ABSPATH . 'wp-content/plugins/acme-core/acme-core.php';

foreach (['use_block_editor_for_post', 'use_block_editor_for_post_type', 'gutenberg_can_edit_post_type'] as $hook) {
    assertion(isset($GLOBALS['wp_filters'][$hook]), "missing block-editor disable filter $hook");
    assertion($GLOBALS['wp_filters'][$hook][0][0] === '__return_false', "filter $hook does not disable block editor");
}
assertion(isset($GLOBALS['wp_actions']['init']), 'property CPT init hook not registered');
assertion(isset($GLOBALS['wp_actions']['add_meta_boxes_property']), 'classic meta-box hook not registered');
assertion(isset($GLOBALS['wp_actions']['save_post_property']), 'property save hook not registered');

acme_register_property_cpt();
assertion(isset($GLOBALS['wp_post_types']['property']), 'property CPT not registered at runtime');
assertion($GLOBALS['wp_post_types']['property']['show_in_rest'] === false, 'property CPT unexpectedly exposed to block REST editor');

acme_property_meta_box();
assertion(isset($GLOBALS['wp_meta_boxes']['acme-property-reference']), 'classic property meta box not registered');
$post = (object)['ID' => 7];
ob_start();
acme_property_meta_box_render($post);
$rendered = ob_get_clean();
assertion(str_contains($rendered, 'A&amp;B&quot;'), 'meta value was not escaped in rendered output');
assertion(($GLOBALS['nonce_fields']['acme_property_reference_nonce'] ?? null) === 'acme_save_property_reference', 'nonce field/action mismatch');

$_POST = ['acme_property_reference_nonce' => 'nonce-ok', 'acme_property_reference' => ' <b>REF-1</b> '];
$GLOBALS['can_edit'] = true;
acme_save_property_reference(7);
assertion(($GLOBALS['wp_updates'][7]['_acme_property_reference'] ?? null) === 'REF-1', 'sanitized authorized save did not persist expected value');

$before = $GLOBALS['wp_updates'][7]['_acme_property_reference'];
$_POST = ['acme_property_reference_nonce' => 'nonce-ok', 'acme_property_reference' => 'UNAUTHORIZED'];
$GLOBALS['can_edit'] = false;
acme_save_property_reference(7);
assertion($GLOBALS['wp_updates'][7]['_acme_property_reference'] === $before, 'capability gate failed to block unauthorized update');

$_POST = ['acme_property_reference_nonce' => 'bad-nonce', 'acme_property_reference' => 'BAD-NONCE'];
$GLOBALS['can_edit'] = true;
acme_save_property_reference(7);
assertion($GLOBALS['wp_updates'][7]['_acme_property_reference'] === $before, 'nonce verification failed to block invalid update');

echo "PASS WordPress PHP runtime contract\n";
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
        "requirements": requirements, "architecture": architecture,
        "style": style, "functions": functions, "plugin": plugin,
        "tests": tests, "runtime_test": runtime_test,
        "config": config, "schema": schema, "deps": deps,
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
    require((gstack / "scripts" / "run-wordpress-specialist-check.py").is_file(),
            "gstack executable WordPress specialist check surface is missing")
    release = integration.partition("## Release relationship")[2]
    require("accountable human production approval" in release,
            "gstack release relationship lost human production approval boundary")
    require(release.find("accountable human production approval") < release.find("gstack-ship"),
            "gstack ship route appears before human production approval")
    print("PASS: gstack review/security/QA/performance specialists remain distinct, executable and human-gated")


def derive_blueprint_handoff(app: Path, intake_path: Path, intake: dict) -> tuple[Path, Path, list[str]]:
    """Build PREOS inputs from actual governed Blueprint output, not parallel fixture prose."""
    sources = intake.get("sources", [])
    requirements = intake.get("source_requirements", [])
    require(sources and requirements, "Blueprint handoff lacks source inventory or requirements")
    governed_sources = [
        s for s in sources
        if s.get("authority") == "HUMAN_APPROVED" and s.get("status") == "CURRENT"
    ]
    governed_paths = {str(s.get("path")) for s in governed_sources}
    require({"docs/requirements.md", "docs/architecture.md"}.issubset(governed_paths),
            "Blueprint governed source inventory lost requirements/architecture inputs")
    for source in governed_sources:
        artifact = app / str(source["path"])
        require(artifact.is_file(), f"Blueprint governed source missing in app: {source['path']}")
        require(source.get("sha256") == sha256(artifact),
                f"Blueprint source hash does not bind actual source: {source['path']}")

    requirement_ids = [str(r["requirement_id"]) for r in requirements]
    require(len(requirement_ids) == len(set(requirement_ids)), "Blueprint requirement IDs are not unique")
    approved_architecture = intake.get("approved_architecture", {})
    approved_stack = intake.get("approved_stack", {})
    approved_text = recursive_text({"architecture": approved_architecture, "stack": approved_stack})
    for token in ("wordpress", "classic", "custom"):
        require(token in approved_text, f"governed Blueprint approval missing {token} delivery decision")

    contract_dir = app / ".ai-product-delivery" / "project-contract"
    packet_dir = app / ".ai-product-delivery" / "task-packets"
    contract_dir.mkdir(parents=True, exist_ok=True)
    packet_dir.mkdir(parents=True, exist_ok=True)
    contract = contract_dir / "PROJECT-CONTRACT.json"
    contract_payload = {
        "schema_version": "1.0",
        "project_id": "three-repo-wordpress",
        "project_contract_version": "PC-WP-1",
        "blueprint_handoff": {
            "source_intake_artifact": intake_path.relative_to(app).as_posix(),
            "source_intake_sha256": sha256(intake_path),
            "project_mode": intake.get("project_mode"),
            "authority_boundary": intake.get("semantic_extraction", {}).get("authority_boundary"),
        },
        "source_hashes": [
            {"artifact": str(s["path"]), "sha256": str(s["sha256"]), "source_id": str(s["source_id"])}
            for s in governed_sources
        ],
        "source_requirements": requirements,
        "approved_architecture": approved_architecture,
        "approved_stack": approved_stack,
        "classification": {
            "profiles": ["wordpress", "classic-theme", "custom-plugin"],
            "derived_from": "SOURCE-INTAKE.approved_architecture+approved_stack",
            "production_assurance": "standard",
        },
        "authority": {
            "production_release": "Accountable Product Owner",
            "authority_source": "governed disposable acceptance fixture; not AI authority",
        },
    }
    write(contract, json.dumps(contract_payload, indent=2, ensure_ascii=False) + "\n")

    packet = packet_dir / "TP-WP-001.md"
    requirement_lines = "\n".join(
        f"- `{r['requirement_id']}` from `{r['source_id']}`: {r['original_wording']}"
        for r in requirements
    )
    packet_text = f"""# TP-WP-001

Blueprint source intake: `{intake_path.relative_to(app).as_posix()}`  
Blueprint source intake SHA-256: `{sha256(intake_path)}`

## Source and requirements

{requirement_lines}

## Scope

Bounded implementation derived from the governed requirements above: implement the `property` custom post type and classic meta-field workflow only in `wp-content/plugins/acme-core/acme-core.php`. Preserve the Blueprint-approved classic-theme/custom-plugin architecture; do not introduce Gutenberg, block themes, Full Site Editing, page builders, or block-based custom-post editing.

## Required checks

- `python tests/test_wordpress_contract.py` must pass.
- `php -l` must pass for every PHP implementation file.
- `php tests/wordpress_runtime_contract.php` must execute the actual theme/plugin and pass.
- gstack-review, gstack-cso, gstack-qa, and gstack-benchmark executable specialist checks must each pass independently.

## Required evidence

- `E-WP-REVIEW` from gstack-review.
- `E-WP-SECURITY` from gstack-cso.
- `E-WP-QA` from gstack-qa.
- `E-WP-PERFORMANCE` from gstack-benchmark.

## Authority

Deployment and production authorization remain human-only. This packet does not authorize release.
"""
    write(packet, packet_text)
    require(all(rid in packet_text for rid in requirement_ids),
            "Task Packet failed to carry every Blueprint requirement ID into PREOS")
    require(contract_payload["blueprint_handoff"]["source_intake_sha256"] == sha256(intake_path),
            "Project Contract lost exact Blueprint SOURCE-INTAKE binding")
    print("PASS: PREOS Project Contract and Task Packet are derived from exact governed Blueprint SOURCE-INTAKE output")
    return contract, packet, requirement_ids


def run_specialists(gstack: Path, app: Path, paths: dict[str, Path], artifact_dir: Path) -> dict[str, dict]:
    runner = gstack / "scripts" / "run-wordpress-specialist-check.py"
    definitions = {
        "E-WP-REVIEW": ("review", "gstack-review"),
        "E-WP-SECURITY": ("cso", "gstack-cso"),
        "E-WP-QA": ("qa", "gstack-qa"),
        "E-WP-PERFORMANCE": ("benchmark", "gstack-benchmark"),
    }
    results: dict[str, dict] = {}
    for evidence_id, (specialist, producer) in definitions.items():
        artifact = artifact_dir / f"{evidence_id}.json"
        proc = run([
            sys.executable, str(runner), "--specialist", specialist,
            "--repo", str(app), "--gstack", str(gstack),
            "--plugin", str(paths["plugin"]),
            "--contract-test", str(paths["tests"]),
            "--runtime-test", str(paths["runtime_test"]),
            "--output", str(artifact),
        ], cwd=gstack)
        result = json.loads(read(artifact))
        require(result.get("result") == "PASS", f"{producer} executable specialist did not pass")
        require(result.get("producer") == producer, f"{specialist} evidence producer identity mismatch")
        require(result.get("checks"), f"{producer} emitted no executed checks")
        require(result.get("production_authority") == "NOT_GRANTED_BY_SPECIALIST",
                f"{producer} crossed production authority boundary")
        require("PASS" in proc.stdout, f"{producer} executable specialist did not report execution result")
        results[evidence_id] = result
    require(len({r["producer"] for r in results.values()}) == 4,
            "specialist execution did not preserve four distinct producers")
    print("PASS: four distinct gstack specialist mechanisms executed and emitted machine-generated evidence")
    return results


def wordpress_e2e(blueprint: Path, preos: Path, gstack: Path) -> None:
    source_intake = blueprint / "scripts" / "source_intake.py"
    preos_scripts = preos / "scripts"
    specialist_runner = gstack / "scripts" / "run-wordpress-specialist-check.py"
    for required in [
        source_intake, specialist_runner,
        preos_scripts / "init-project-state.py",
        preos_scripts / "checkpoint-state.py",
        preos_scripts / "recover-state.py",
        preos_scripts / "capture-evidence.py",
        preos_scripts / "validate-evidence.py",
        preos_scripts / "evaluate-gates.py",
        preos_scripts / "record-approval.py",
    ]:
        require(required.is_file(), f"required executable contract missing: {required}")
    php_version = run(["php", "--version"], cwd=gstack)
    require("PHP" in php_version.stdout, "PHP CLI is required for executable WordPress acceptance")

    with tempfile.TemporaryDirectory(prefix="three-repo-wordpress-e2e-") as td:
        base = Path(td)
        app = base / "wordpress-app"
        app.mkdir()
        paths = create_wordpress_fixture(app)

        decisions = base / "source-decisions.json"
        write(decisions, json.dumps({
            "project_mode": "BROWNFIELD",
            "source_decisions": [
                {"path": "docs/requirements.md", "authority": "HUMAN_APPROVED", "status": "CURRENT"},
                {"path": "docs/architecture.md", "authority": "HUMAN_APPROVED", "status": "CURRENT"},
                {"path": "wp-content/themes/acme-classic/functions.php", "authority": "IMPLEMENTATION_EVIDENCE", "status": "CURRENT"},
                {"path": "wp-content/plugins/acme-core/acme-core.php", "authority": "IMPLEMENTATION_EVIDENCE", "status": "CURRENT"},
            ],
            "approved_architecture": {
                "cms": "WordPress", "theme_model": "classic PHP theme",
                "extension_model": "custom-code plugin", "block_editor": "disabled",
                "full_site_editing": "disabled",
            },
            "approved_stack": {
                "cms": "WordPress", "language": "PHP",
                "theme": "classic", "plugin": "custom-code",
            },
            "unknowns": [], "assumptions": [], "role_gaps": [],
            "human_decisions_required": [],
        }, indent=2) + "\n")

        intake_proc = run([
            sys.executable, str(source_intake), str(app),
            "--project-root", str(app), "--decisions", str(decisions),
            "--intent", "disposable WordPress classic-theme custom-plugin three-repository acceptance",
        ], cwd=blueprint)
        intake_path = app / ".ai-product-delivery" / "source-intake" / "SOURCE-INTAKE.json"
        intake = json.loads(read(intake_path))
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
                "Blueprint did not observe WordPress + PHP from implementation evidence")
        declared_arch = recursive_text(intake.get("declared_architecture", {}))
        require("wordpress" in declared_arch and "classic" in declared_arch,
                "Blueprint did not extract declared classic WordPress architecture")
        semantic = intake.get("semantic_extraction", {})
        require(semantic.get("automatic_approval") is False,
                "automatic extraction incorrectly crossed the approval boundary")
        require(intake.get("approved_architecture", {}).get("theme_model") == "classic PHP theme",
                "governed approved architecture was not preserved separately")
        print("PASS: Blueprint extracts WordPress requirements/architecture/stack without automatic approval")

        contract, packet, requirement_ids = derive_blueprint_handoff(app, intake_path, intake)

        git(app, "init")
        git(app, "config", "user.email", "wordpress-e2e@example.invalid")
        git(app, "config", "user.name", "WordPress E2E")
        git(app, "add", ".")
        git(app, "commit", "-m", "governed Blueprint-derived WordPress baseline")

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
            "--next-unverified-action", "WordPress executable contracts",
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
                "disposable WordPress structural contract did not pass")
        for php in sorted(app.rglob("*.php")):
            run(["php", "-l", str(php)], cwd=app)
        php_runtime = run(["php", str(paths["runtime_test"])], cwd=app)
        require("PASS WordPress PHP runtime contract" in php_runtime.stdout,
                "actual PHP theme/plugin runtime contract did not pass")
        print("PASS: actual PHP syntax and WordPress-API-stub runtime behavior verified")

        git(app, "add", "wp-content/plugins/acme-core/acme-core.php")
        git(app, "commit", "-m", "implement bounded classic WordPress custom plugin")
        require(git(app, "status", "--porcelain") == "", "implementation repository must be clean before evidence")

        artifact_dir = base / "specialist-evidence"
        artifact_dir.mkdir()
        specialist_results = run_specialists(gstack, app, paths, artifact_dir)
        specialist_defs = {
            "E-WP-REVIEW": ("review", "gstack-review"),
            "E-WP-SECURITY": ("cso", "gstack-cso"),
            "E-WP-QA": ("qa", "gstack-qa"),
            "E-WP-PERFORMANCE": ("benchmark", "gstack-benchmark"),
        }
        evidence_paths: list[Path] = []
        for evidence_id, (specialist, producer) in specialist_defs.items():
            result = specialist_results[evidence_id]
            artifact = artifact_dir / f"{evidence_id}.json"
            skill_contract = gstack / str(result["skill_contract"])
            capture = [
                sys.executable, str(preos_scripts / "capture-evidence.py"),
                "three-repo-wordpress", evidence_id, "--repo", str(app),
                "--producer", producer, "--environment", "disposable-wordpress-e2e",
                "--artifact", str(artifact), "--project-contract", str(contract),
                "--task-packet", str(packet), "--source", str(paths["requirements"]),
                "--source", str(paths["architecture"]), "--config", str(paths["config"]),
                "--schema", str(paths["schema"]), "--dependency", str(paths["deps"]),
                "--test-definition", str(paths["tests"]),
                "--test-definition", str(paths["runtime_test"]),
                "--test-definition", str(specialist_runner),
                "--test-definition", str(skill_contract),
                "--env-var", "WP_ENVIRONMENT_TYPE",
                "--test-or-command", f"python scripts/run-wordpress-specialist-check.py --specialist {specialist}",
                "--result", str(result["result"]),
            ]
            for requirement_id in requirement_ids:
                capture.extend(["--requirement-id", requirement_id])
            run(capture, cwd=preos, env=env)
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
        print("PASS: executed specialist records are commit/source/contract/task/config/schema/dependency/test/environment bound")

        verification = base / "hard-verification.json"
        check_specs = {
            "E-WP-REVIEW": "gstack-review executable bounded-diff/classic-theme review",
            "E-WP-SECURITY": "gstack-cso executable PHP/security/runtime review",
            "E-WP-QA": "gstack-qa executable syntax/structural/runtime test",
            "E-WP-PERFORMANCE": "gstack-benchmark executable runtime measurement",
        }
        write(verification, json.dumps({
            "schema_version": "1.0",
            "checks": [
                {
                    "id": evidence_id.lower().replace("e-wp-", ""),
                    "status": specialist_results[evidence_id]["result"],
                    "command_or_test": check_specs[evidence_id],
                    "evidence_id": evidence_id,
                }
                for evidence_id in sorted(specialist_results)
            ],
            "evidence_ids": sorted(specialist_results),
            "traceability": "UPDATED",
            "rollback_point": git(app, "rev-parse", "HEAD"),
        }, indent=2) + "\n")

        hard = run([
            sys.executable, str(preos_scripts / "checkpoint-state.py"),
            "three-repo-wordpress", "--repo", str(app), "--kind", "hard",
            "--event", "IMPLEMENTATION_COMPLETE", "--project-contract", str(contract),
            "--project-contract-version", "PC-WP-1", "--task-packet", str(packet),
            "--task-packet-id", "TP-WP-001",
            "--last-verified-action", "WordPress executable contracts and independent specialist evidence verified",
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
            "G10": ["E-WP-SECURITY"], "G11": sorted(specialist_results),
        }
        gates_in = base / "wordpress-gates.json"
        gates_out = base / "wordpress-gates-out.json"
        write(gates_in, json.dumps({
            "gates": {
                gid: [{
                    "state": "GREEN", "evidence_ids": gate_evidence[gid],
                    "source": "disposable-wordpress-three-repo-e2e",
                }]
                for gid in [f"G{i}" for i in range(12)]
            }
        }, indent=2) + "\n")
        run([
            sys.executable, str(preos_scripts / "evaluate-gates.py"),
            str(gates_in), "--output", str(gates_out),
        ], cwd=preos, env=env)
        gate_results = json.loads(read(gates_out))["gate_results"]
        expected_gates = [f"G{i}" for i in range(12)]
        require(list(gate_results) == expected_gates, "PREOS gate output is not exact G0-G11")
        require(all(gate_results[g]["state"] == "GREEN" for g in expected_gates),
                "strictly evidenced disposable WordPress gate chain did not evaluate GREEN")
        print("PASS: executed specialist evidence flows through exact PREOS G0-G11 gate mechanics")

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
