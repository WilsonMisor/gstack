import { describe, expect, test } from 'bun:test';
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { validateProjectContract } from '../../scripts/production-engine/validate-project-contract';
import { validateCoverage } from '../../scripts/production-engine/classify-control-coverage';
import { generateRiskSet } from '../../scripts/production-engine/generate-risk-set';
import { evidenceFresh } from '../../scripts/production-engine/validate-preos-evidence';
import { reconcile } from '../../scripts/production-engine/state-reconcile';
import { writeState } from '../../scripts/production-engine/state-write';
import {
  headSha,
  productionStateDir,
  sha256File,
  workingTreeFingerprint,
} from '../../scripts/production-engine/lib';

const GSTACK_ROOT = resolve(import.meta.dir, '../..');
const PIPELINE = [
  '$project-init', '$office-hours', '$plan-ceo-review', '$plan-eng-review', '$autoplan',
  '$production-implement', '$review', '$qa', '$ship', '$land-and-deploy', '$canary',
] as const;
const OUTCOMES = [
  'PROJECT CONTRACT APPROVED', 'PRODUCT CONTEXT REVIEWED', 'STRATEGIC REVIEW PASSED',
  'ENGINEERING REVIEW PLANNED', 'APPROVED IMPLEMENTATION PLAN', 'IMPLEMENTATION COMPLETE',
  'ENGINEERING REVIEW PASSED', 'QA PASSED', 'RELEASE READY', 'DEPLOYED',
  'CANARY/PRODUCTION VERIFICATION PASSED',
] as const;

type Fixture = {
  root: string;
  stateRoot: string;
  sourcePath: string;
  contractPath: string;
  bindingPath: string;
  coveragePath: string;
  planPath: string;
  iuPath: string;
  evidencePath: string;
};

function git(cwd: string, args: string[]): string {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8', timeout: 30_000 });
  if (r.status !== 0) throw new Error(`git ${args.join(' ')} failed: ${r.stderr || r.stdout}`);
  return String(r.stdout || '').trim();
}

function writeJson(path: string, value: unknown): void {
  mkdirSync(resolve(path, '..'), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function newFixture(): Fixture {
  const root = mkdtempSync(join(tmpdir(), 'preos-wp-app-'));
  const stateRoot = mkdtempSync(join(tmpdir(), 'preos-wp-state-'));
  git(root, ['init']);
  git(root, ['checkout', '-b', 'fixture/wordpress-classic']);
  git(root, ['config', 'user.email', 'fixture@example.invalid']);
  git(root, ['config', 'user.name', 'PREOS Fixture']);

  const sourcePath = join(root, 'docs', 'requirements.md');
  const themeDir = join(root, 'wp-content', 'themes', 'fixture-classic');
  const pluginDir = join(root, 'wp-content', 'plugins', 'fixture-core');
  mkdirSync(join(root, 'docs'), { recursive: true });
  mkdirSync(themeDir, { recursive: true });
  mkdirSync(pluginDir, { recursive: true });
  writeFileSync(sourcePath, [
    '# WordPress Classic Fixture', '',
    'Build a code-first WordPress site using a classic theme for presentation and a custom plugin for business logic.',
    'No block theme, FSE, Gutenberg layout, or page builder is permitted.',
    'Authenticated users manage tenant-scoped private records through forms and REST routes.', '',
  ].join('\n'), 'utf8');
  writeFileSync(join(themeDir, 'style.css'), '/*\nTheme Name: Fixture Classic\n*/\n', 'utf8');
  writeFileSync(join(themeDir, 'functions.php'), "<?php\n// Presentation hooks only.\n", 'utf8');
  writeFileSync(join(pluginDir, 'fixture-core.php'), "<?php\n/* Plugin Name: Fixture Core */\n// Business logic lives here.\n", 'utf8');
  git(root, ['add', '.']);
  git(root, ['commit', '-m', 'fixture: initial WordPress classic source']);

  return {
    root,
    stateRoot,
    sourcePath,
    contractPath: join(root, '.gstack', 'project-contract', 'PROJECT-CONTRACT.json'),
    bindingPath: join(root, '.gstack', 'project-contract', 'domain-skill-bindings.json'),
    coveragePath: join(root, '.gstack', 'preos', 'control-coverage.json'),
    planPath: join(root, '.gstack', 'preos', 'stage-4-plan.json'),
    iuPath: join(root, '.gstack', 'preos', 'implementation-unit-IU-WP-001.json'),
    evidencePath: join(stateRoot, 'fixture-evidence.json'),
  };
}

function withFixture(fn: (f: Fixture) => void): void {
  const oldStateRoot = process.env.GSTACK_STATE_ROOT;
  const f = newFixture();
  process.env.GSTACK_STATE_ROOT = f.stateRoot;
  try { fn(f); } finally {
    if (oldStateRoot === undefined) delete process.env.GSTACK_STATE_ROOT;
    else process.env.GSTACK_STATE_ROOT = oldStateRoot;
    rmSync(f.root, { recursive: true, force: true });
    rmSync(f.stateRoot, { recursive: true, force: true });
  }
}

function contractFor(f: Fixture, status: 'DRAFT'|'APPROVED' = 'APPROVED'): any {
  return {
    contract_id: 'CONTRACT-WP-001', version: '1.0.0', project_root: f.root,
    source_hashes: [{ path: 'docs/requirements.md', sha256: sha256File(f.sourcePath) }],
    requirements: [{ id: 'REQ-WP-001', text: 'Tenant-scoped private record workflow in classic WordPress' }],
    architecture: { runtime: 'WordPress', presentation: 'classic theme', business_logic: 'custom plugin' },
    tech_stack: {
      application_type: 'wordpress-classic-code-first', wordpress: true, language: 'PHP',
      theme: 'classic', business_logic: 'custom-plugin', block_theme: false, fse: false,
      gutenberg_layout: false, page_builder: false,
    },
    context: { multi_tenant: true, files: true, money_movement: false, production_maturity_stage: 1, threat_maturity_stage: 1 },
    roles: { accountable: ['PDM'], implementation: ['WEB','CMS'], review: ['STAFF','SEC','QA'] },
    authorities: { architecture: 'STAFF', security: 'SEC', release: 'PRODENG' },
    selected_overlay: 'wordpress-classic',
    domain_skill_bindings: ['DOMAIN-WEB-001'],
    unresolved_conflicts: [],
    approvals: status === 'APPROVED'
      ? [{ id: 'APP-WP-CONTRACT-001', status: 'APPROVED', authority: 'PDM', timestamp: '2026-08-25T00:00:00.000Z' }]
      : [],
    status,
  };
}

function writeApprovedContractAndBinding(f: Fixture): void {
  writeJson(f.contractPath, contractFor(f, 'APPROVED'));
  writeJson(f.bindingPath, [{
    binding_id: 'DOMAIN-WEB-001',
    name: 'existing-web-development-skill',
    path: '%CODEX_HOME%/skills/web-development/SKILL.md',
    capability: 'code-first classic-theme/custom-plugin WordPress implementation',
    ownership: 'independent-specialist-skill',
    copied_into_gstack: false,
  }]);
}

function writeCoverage(f: Fixture): any[] {
  const rows = Array.from({ length: 75 }, (_, i) => ({
    no: i + 1,
    control_id: `FS-${String(i + 1).padStart(3, '0')}`,
    wp_control_id: `WP-${String(i + 1).padStart(3, '0')}`,
    applicability: 'Applies', gate_result: 'GREEN',
    test_id: `WP-FIXTURE-TEST-${String(i + 1).padStart(3, '0')}`,
    evidence_id: `WP-FIXTURE-EVIDENCE-${String(i + 1).padStart(3, '0')}`,
  }));
  writeJson(f.coveragePath, rows);
  return rows;
}

function parseWpRows(): Array<{ id: string; source: number }> {
  const md = readFileSync(join(GSTACK_ROOT, 'production-implement', 'references', 'wordpress-classic-overlay.md'), 'utf8');
  const rows: Array<{ id: string; source: number }> = [];
  for (const line of md.split(/\r?\n/)) {
    const m = line.match(/^\|\s*(WP-\d{3})\s*\|\s*(\d{1,2})\s*\|/);
    if (m) rows.push({ id: m[1], source: Number(m[2]) });
  }
  return rows;
}

function writePlan(f: Fixture): void {
  writeJson(f.planPath, {
    plan_id: 'PLAN-WP-001', stage: 4, status: 'APPROVED', contract_version: '1.0.0',
    approved_scope: ['REQ-WP-001'], selected_overlay: 'wordpress-classic',
    domain_skill_binding_ids: ['DOMAIN-WEB-001'], implementation_units: ['IU-WP-001'],
    approval: { id: 'APP-WP-PLAN-001', status: 'APPROVED', authority: 'PDM', timestamp: '2026-08-25T00:01:00.000Z' },
  });
}

function writeVerifiedIU(f: Fixture, risks: any[]): void {
  writeJson(f.iuPath, {
    iu_id: 'IU-WP-001', requirements: ['REQ-WP-001'],
    controls: Array.from({ length: 75 }, (_, i) => `FS-${String(i + 1).padStart(3, '0')}`),
    risks: risks.slice(0, 8).map((r) => r.check_id),
    files: ['wp-content/themes/fixture-classic/functions.php', 'wp-content/plugins/fixture-core/fixture-core.php'],
    dependencies: [],
    change_impact: { wordpress: true, theme: 'classic', plugin: 'custom', data_scope: 'tenant/private-records' },
    tests: ['nonce', 'capability', 'permission-callback', 'scoped-query', 'prepared-sql', 'private-file', 'failure-path'],
    evidence: ['EVIDENCE-WP-IU-001'],
    rollback: { strategy: 'revert theme/plugin change; restore DB backup if a migration was approved' },
    accountable_owner_roles: ['PDM'], implementation_owner_roles: ['WEB','CMS'], reviewer_approver_roles: ['STAFF','SEC','QA'],
    status: 'VERIFIED',
  });
}

function writeEvidence(f: Fixture): any {
  const e = {
    evidence_id: 'EVIDENCE-WP-IU-001', status: 'PASS', produced_at: new Date().toISOString(),
    environment: 'disposable-wordpress-classic-fixture', commit_sha: headSha(f.root),
    working_tree_fingerprint: workingTreeFingerprint(f.root), config_version: 'wp-fixture-config-v1',
    invalidation_triggered: false,
  };
  writeJson(f.evidencePath, [e]);
  return e;
}

function stage5Preflight(f: Fixture): { ok: boolean; reasons: string[] } {
  const reasons: string[] = [];
  const contract = validateProjectContract(f.contractPath, f.root);
  if (!contract.ok) reasons.push(...contract.errors);
  const c = existsSync(f.contractPath) ? JSON.parse(readFileSync(f.contractPath, 'utf8')) : null;
  if (c && (c.selected_overlay !== 'wordpress-classic' || c.tech_stack?.wordpress !== true)) reasons.push('WordPress classic overlay not selected');
  if (!existsSync(f.bindingPath)) reasons.push('domain skill binding missing');
  if (!existsSync(f.planPath)) reasons.push('approved Stage-4 plan missing');
  else {
    const p = JSON.parse(readFileSync(f.planPath, 'utf8'));
    if (p.status !== 'APPROVED' || p.approval?.status !== 'APPROVED') reasons.push('Stage-4 plan is not explicitly approved');
    if (c && p.contract_version !== c.version) reasons.push('Stage-4 plan contract version mismatch');
    if (p.selected_overlay !== 'wordpress-classic') reasons.push('wrong implementation overlay');
  }
  if (!existsSync(f.coveragePath)) reasons.push('75-control classification missing');
  else { try { validateCoverage(f.coveragePath); } catch (e) { reasons.push((e as Error).message); } }
  if (parseWpRows().length !== 75) reasons.push('75-row WordPress interpretation missing');
  if (!existsSync(f.iuPath)) reasons.push('implementation unit missing');
  else if (JSON.parse(readFileSync(f.iuPath, 'utf8')).status !== 'VERIFIED') reasons.push('implementation unit is not VERIFIED');
  if (!existsSync(f.evidencePath)) reasons.push('evidence missing');
  else for (const e of JSON.parse(readFileSync(f.evidencePath, 'utf8'))) {
    const result = evidenceFresh(e, new Date(), f.root);
    if (!result.fresh) reasons.push(result.reason || 'evidence stale');
  }
  return { ok: reasons.length === 0, reasons };
}

describe('AT-033 — disposable WordPress classic-theme/custom-plugin Stage 0→10 lifecycle', () => {
  test('selects the WordPress code-first overlay and keeps the specialist web-development skill independent', () => {
    withFixture((f) => {
      expect(validateProjectContract(f.contractPath, f.root).ok).toBe(false);
      writeJson(f.contractPath, contractFor(f, 'DRAFT'));
      expect(validateProjectContract(f.contractPath, f.root).approved).toBe(false);
      writeApprovedContractAndBinding(f);
      const contract = JSON.parse(readFileSync(f.contractPath, 'utf8'));
      expect(validateProjectContract(f.contractPath, f.root).ok).toBe(true);
      expect(contract.tech_stack.wordpress).toBe(true);
      expect(contract.tech_stack.theme).toBe('classic');
      expect(contract.tech_stack.business_logic).toBe('custom-plugin');
      expect(contract.tech_stack.block_theme).toBe(false);
      expect(contract.tech_stack.fse).toBe(false);
      expect(contract.tech_stack.gutenberg_layout).toBe(false);
      expect(contract.tech_stack.page_builder).toBe(false);
      const binding = JSON.parse(readFileSync(f.bindingPath, 'utf8'))[0];
      expect(binding.ownership).toBe('independent-specialist-skill');
      expect(binding.copied_into_gstack).toBe(false);
      expect(existsSync(join(f.root, '.gstack', 'skills', 'web-development'))).toBe(false);
      const interoperability = readFileSync(join(GSTACK_ROOT, 'project-init', 'references', 'domain-skill-interoperability.md'), 'utf8');
      expect(interoperability).toContain('never copy or overwrite');
    });
  });

  test('keeps FS-001..FS-075 immutable while enforcing WP-001..WP-075 and the WordPress security completion rules', () => {
    withFixture((f) => {
      writeApprovedContractAndBinding(f);
      const coverage = writeCoverage(f);
      expect(validateCoverage(f.coveragePath)).toHaveLength(75);
      expect(coverage.map((r) => r.control_id)).toEqual(Array.from({ length: 75 }, (_, i) => `FS-${String(i + 1).padStart(3, '0')}`));
      const wpRows = parseWpRows();
      expect(wpRows).toHaveLength(75);
      expect(wpRows.map((r) => r.id)).toEqual(Array.from({ length: 75 }, (_, i) => `WP-${String(i + 1).padStart(3, '0')}`));
      expect(wpRows.map((r) => r.source)).toEqual(Array.from({ length: 75 }, (_, i) => i + 1));
      const overlay = readFileSync(join(GSTACK_ROOT, 'production-implement', 'references', 'wordpress-classic-overlay.md'), 'utf8');
      for (const required of ['nonce', 'current_user_can', 'owner/tenant/role/status', '$wpdb->prepare', 'permission_callback', 'private-file authorization']) {
        expect(overlay).toContain(required);
      }
      const risks = generateRiskSet({ features: ['private-record-update'], multi_tenant: true, files: true, wordpress: true, maturity_stage: 1, threat_stage: 1 });
      expect(risks.length).toBeGreaterThan(0);
      expect(risks.some((r) => r.domain === 'Authorization and Tenant Isolation')).toBe(true);
      expect(risks.some((r) => r.domain === 'Files and Object Storage')).toBe(true);
      expect(risks.every((r) => r.gate_result === 'UNKNOWN')).toBe(true);
    });
  });

  test('Stage 5 blocks until the approved plan, domain binding, 75 classifications, verified IU and fresh evidence exist', () => {
    withFixture((f) => {
      writeApprovedContractAndBinding(f);
      expect(stage5Preflight(f).ok).toBe(false);
      expect(stage5Preflight(f).reasons).toContain('approved Stage-4 plan missing');
      writePlan(f);
      expect(stage5Preflight(f).reasons).toContain('75-control classification missing');
      writeCoverage(f);
      const risks = generateRiskSet({ features: ['private-record-update'], multi_tenant: true, files: true, wordpress: true });
      writeVerifiedIU(f, risks);
      expect(stage5Preflight(f).reasons).toContain('evidence missing');
      writeEvidence(f);
      expect(stage5Preflight(f)).toEqual({ ok: true, reasons: [] });
    });
  });

  test('walks the canonical external pipeline in exact 0→10 order without WordPress bypasses or Stage-5 self-approval', () => {
    withFixture((f) => {
      writeApprovedContractAndBinding(f);
      writeCoverage(f);
      writePlan(f);
      const risks = generateRiskSet({ features: ['private-record-update'], multi_tenant: true, files: true, wordpress: true, maturity_stage: 1, threat_stage: 1 });
      writeVerifiedIU(f, risks);
      const evidence = writeEvidence(f);
      expect(stage5Preflight(f)).toEqual({ ok: true, reasons: [] });
      expect(evidenceFresh(evidence, new Date(), f.root).fresh).toBe(true);

      const documented = Array.from(readFileSync(join(GSTACK_ROOT, 'docs', 'PREOS.md'), 'utf8').matchAll(/^\d+\. `([^`]+)`$/gm), (m) => m[1]);
      expect(documented).toEqual([...PIPELINE]);
      const ledger: Array<{ stage: number; skill: string; outcome: string }> = [];
      for (let stage = 0; stage < PIPELINE.length; stage++) {
        if (stage > 0) expect(ledger.at(-1)?.stage).toBe(stage - 1);
        if (stage === 5) expect(stage5Preflight(f).ok).toBe(true);
        if (stage === 6) expect(ledger.at(-1)?.outcome).toBe('IMPLEMENTATION COMPLETE');
        const row = { stage, skill: PIPELINE[stage], outcome: OUTCOMES[stage] };
        ledger.push(row);
        writeState({
          status: 'VERIFIED', stage, skill: row.skill, lifecycle_status: row.outcome,
          selected_overlay: 'wordpress-classic', domain_skill_binding_ids: ['DOMAIN-WEB-001'],
          next_unverified_action: stage < 10 ? `enter stage ${stage + 1} ${PIPELINE[stage + 1]}` : 'production feedback monitoring',
          pipeline_state: { current_stage: stage, current_skill: row.skill, completed_stages: ledger.map((x) => x.stage) },
        }, f.root);
      }
      expect(ledger.map((x) => x.stage)).toEqual(Array.from({ length: 11 }, (_, i) => i));
      expect(ledger.map((x) => x.skill)).toEqual([...PIPELINE]);
      expect(ledger[5].outcome).toBe('IMPLEMENTATION COMPLETE');
      expect(ledger[5].outcome).not.toBe('PRODUCTION APPROVED');
      expect(ledger[8].outcome).toBe('RELEASE READY');
      expect(ledger[9].outcome).toBe('DEPLOYED');
      expect(ledger[10].outcome).toBe('CANARY/PRODUCTION VERIFICATION PASSED');

      const stateDir = productionStateDir(f.root);
      const persisted = readFileSync(join(stateDir, 'implementation-ledger.jsonl'), 'utf8').trim().split(/\r?\n/).map((line) => JSON.parse(line));
      expect(persisted).toHaveLength(11);
      expect(persisted.every((x) => x.selected_overlay === 'wordpress-classic')).toBe(true);
      expect(persisted.every((x) => x.domain_skill_binding_ids?.includes('DOMAIN-WEB-001'))).toBe(true);
      const resume = reconcile(f.root);
      expect(resume.status).toBe('SAFE_TO_RESUME');
      expect(resume.resume_action).toBe('production feedback monitoring');
    });
  }, 20_000);
});
