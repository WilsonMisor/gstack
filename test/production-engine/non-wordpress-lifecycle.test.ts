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
  '$project-init',
  '$office-hours',
  '$plan-ceo-review',
  '$plan-eng-review',
  '$autoplan',
  '$production-implement',
  '$review',
  '$qa',
  '$ship',
  '$land-and-deploy',
  '$canary',
] as const;

const STAGE_OUTCOMES = [
  'PROJECT CONTRACT APPROVED',
  'PRODUCT CONTEXT REVIEWED',
  'STRATEGIC REVIEW PASSED',
  'ENGINEERING REVIEW PLANNED',
  'APPROVED IMPLEMENTATION PLAN',
  'IMPLEMENTATION COMPLETE',
  'ENGINEERING REVIEW PASSED',
  'QA PASSED',
  'RELEASE READY',
  'DEPLOYED',
  'CANARY/PRODUCTION VERIFICATION PASSED',
] as const;

type Fixture = {
  root: string;
  stateRoot: string;
  sourcePath: string;
  contractPath: string;
  coveragePath: string;
  planPath: string;
  iuPath: string;
  evidencePath: string;
};

function git(cwd: string, args: string[]): string {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8', timeout: 30_000 });
  if (r.status !== 0) {
    throw new Error(`git ${args.join(' ')} failed: ${r.stderr || r.stdout}`);
  }
  return String(r.stdout || '').trim();
}

function writeJson(path: string, value: unknown): void {
  mkdirSync(resolve(path, '..'), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

function newFixture(): Fixture {
  const root = mkdtempSync(join(tmpdir(), 'preos-nonwp-app-'));
  const stateRoot = mkdtempSync(join(tmpdir(), 'preos-nonwp-state-'));
  git(root, ['init']);
  git(root, ['checkout', '-b', 'fixture/non-wordpress']);
  git(root, ['config', 'user.email', 'fixture@example.invalid']);
  git(root, ['config', 'user.name', 'PREOS Fixture']);

  const sourcePath = join(root, 'docs', 'requirements.md');
  const appPath = join(root, 'src', 'service.ts');
  mkdirSync(join(root, 'docs'), { recursive: true });
  mkdirSync(join(root, 'src'), { recursive: true });
  writeFileSync(
    sourcePath,
    [
      '# Account Service Fixture',
      '',
      'Build a non-WordPress TypeScript REST service backed by PostgreSQL.',
      'Users can register, sign in and update a tenant-scoped profile.',
      'The fixture has no payment movement, CMS, page-builder or WordPress runtime.',
      '',
    ].join('\n'),
    'utf8',
  );
  writeFileSync(appPath, "export const fixture = 'non-wordpress';\n", 'utf8');
  git(root, ['add', '.']);
  git(root, ['commit', '-m', 'fixture: initial application source']);

  return {
    root,
    stateRoot,
    sourcePath,
    contractPath: join(root, '.gstack', 'project-contract', 'PROJECT-CONTRACT.json'),
    coveragePath: join(root, '.gstack', 'preos', 'control-coverage.json'),
    planPath: join(root, '.gstack', 'preos', 'stage-4-plan.json'),
    iuPath: join(root, '.gstack', 'preos', 'implementation-unit-IU-001.json'),
    evidencePath: join(stateRoot, 'fixture-evidence.json'),
  };
}

function cleanupFixture(f: Fixture, oldStateRoot: string | undefined): void {
  if (oldStateRoot === undefined) delete process.env.GSTACK_STATE_ROOT;
  else process.env.GSTACK_STATE_ROOT = oldStateRoot;
  rmSync(f.root, { recursive: true, force: true });
  rmSync(f.stateRoot, { recursive: true, force: true });
}

function withFixture(fn: (f: Fixture) => void): void {
  const oldStateRoot = process.env.GSTACK_STATE_ROOT;
  const f = newFixture();
  process.env.GSTACK_STATE_ROOT = f.stateRoot;
  try {
    fn(f);
  } finally {
    cleanupFixture(f, oldStateRoot);
  }
}

function contractFor(f: Fixture, status: 'DRAFT' | 'APPROVED' = 'APPROVED'): any {
  return {
    contract_id: 'CONTRACT-NONWP-001',
    version: '1.0.0',
    project_root: f.root,
    source_hashes: [
      { path: 'docs/requirements.md', sha256: sha256File(f.sourcePath) },
    ],
    requirements: [
      { id: 'REQ-001', text: 'Tenant-scoped account registration, sign-in and profile update' },
    ],
    architecture: {
      style: 'modular service',
      api: 'REST',
      database: 'PostgreSQL',
    },
    tech_stack: {
      application_type: 'non-wordpress',
      language: 'TypeScript',
      runtime: 'Bun',
      api: 'REST',
      database: 'PostgreSQL',
      wordpress: false,
    },
    context: {
      multi_tenant: true,
      money_movement: false,
      files: false,
      queues: false,
      production_maturity_stage: 1,
      threat_maturity_stage: 1,
    },
    roles: {
      accountable: ['PDM'],
      implementation: ['SWE'],
      review: ['STAFF', 'SEC', 'QA'],
    },
    authorities: {
      architecture: 'STAFF',
      security: 'SEC',
      release: 'PRODENG',
    },
    unresolved_conflicts: [],
    approvals: status === 'APPROVED'
      ? [{ id: 'APP-CONTRACT-001', status: 'APPROVED', authority: 'PDM', timestamp: '2026-08-25T00:00:00.000Z' }]
      : [],
    status,
  };
}

function writeApprovedContract(f: Fixture): any {
  const contract = contractFor(f, 'APPROVED');
  writeJson(f.contractPath, contract);
  return contract;
}

function writeControlCoverage(f: Fixture): any[] {
  const rows = Array.from({ length: 75 }, (_, i) => ({
    no: i + 1,
    control_id: `FS-${String(i + 1).padStart(3, '0')}`,
    applicability: 'Applies',
    gate_result: 'GREEN',
    test_id: `FIXTURE-TEST-${String(i + 1).padStart(3, '0')}`,
    evidence_id: `FIXTURE-EVIDENCE-${String(i + 1).padStart(3, '0')}`,
  }));
  writeJson(f.coveragePath, rows);
  return rows;
}

function writeApprovedPlan(f: Fixture): any {
  const plan = {
    plan_id: 'PLAN-NONWP-001',
    stage: 4,
    status: 'APPROVED',
    contract_version: '1.0.0',
    approved_scope: ['REQ-001'],
    selected_overlay: 'non-wordpress',
    implementation_units: ['IU-001'],
    approval: {
      id: 'APP-PLAN-001',
      status: 'APPROVED',
      authority: 'PDM',
      timestamp: '2026-08-25T00:01:00.000Z',
    },
  };
  writeJson(f.planPath, plan);
  return plan;
}

function writeVerifiedImplementationUnit(f: Fixture, risks: any[]): any {
  const iu = {
    iu_id: 'IU-001',
    requirements: ['REQ-001'],
    controls: Array.from({ length: 75 }, (_, i) => `FS-${String(i + 1).padStart(3, '0')}`),
    risks: risks.slice(0, 8).map((r) => r.check_id),
    files: ['src/service.ts'],
    dependencies: [],
    change_impact: {
      api: true,
      database: true,
      wordpress: false,
      notes: 'Non-WordPress REST/API change only',
    },
    tests: ['unit', 'authorization', 'tenant-isolation', 'failure-path'],
    evidence: ['EVIDENCE-IU-001'],
    rollback: { strategy: 'revert application commit; no destructive migration' },
    accountable_owner_roles: ['PDM'],
    implementation_owner_roles: ['SWE'],
    reviewer_approver_roles: ['STAFF', 'SEC', 'QA'],
    status: 'VERIFIED',
  };
  writeJson(f.iuPath, iu);
  return iu;
}

function writeFreshEvidence(f: Fixture): any {
  const record = {
    evidence_id: 'EVIDENCE-IU-001',
    status: 'PASS',
    produced_at: new Date().toISOString(),
    environment: 'disposable-non-wordpress-fixture',
    commit_sha: headSha(f.root),
    working_tree_fingerprint: workingTreeFingerprint(f.root),
    config_version: 'fixture-config-v1',
    invalidation_triggered: false,
  };
  writeJson(f.evidencePath, [record]);
  return record;
}

function stage5Preflight(f: Fixture): { ok: boolean; reasons: string[] } {
  const reasons: string[] = [];
  const contract = validateProjectContract(f.contractPath, f.root);
  if (!contract.ok) reasons.push(...contract.errors);

  if (!existsSync(f.planPath)) {
    reasons.push('approved Stage-4 plan missing');
  } else {
    const plan = JSON.parse(readFileSync(f.planPath, 'utf8'));
    if (plan.status !== 'APPROVED' || plan.approval?.status !== 'APPROVED') {
      reasons.push('Stage-4 plan is not explicitly approved');
    }
    const contractJson = existsSync(f.contractPath)
      ? JSON.parse(readFileSync(f.contractPath, 'utf8'))
      : null;
    if (contractJson && plan.contract_version !== contractJson.version) {
      reasons.push('Stage-4 plan contract version mismatch');
    }
    if (plan.selected_overlay !== 'non-wordpress') reasons.push('wrong implementation overlay');
  }

  if (!existsSync(f.coveragePath)) {
    reasons.push('75-control classification missing');
  } else {
    try {
      validateCoverage(f.coveragePath);
    } catch (e) {
      reasons.push((e as Error).message);
    }
  }

  if (!existsSync(f.iuPath)) {
    reasons.push('implementation unit missing');
  } else {
    const iu = JSON.parse(readFileSync(f.iuPath, 'utf8'));
    if (iu.status !== 'VERIFIED') reasons.push('implementation unit is not VERIFIED');
  }

  if (!existsSync(f.evidencePath)) {
    reasons.push('evidence missing');
  } else {
    const evidence = JSON.parse(readFileSync(f.evidencePath, 'utf8')) as any[];
    for (const record of evidence) {
      const result = evidenceFresh(record, new Date(), f.root);
      if (!result.fresh) reasons.push(result.reason || 'evidence stale');
    }
  }

  return { ok: reasons.length === 0, reasons };
}

describe('AT-032 — disposable non-WordPress Stage 0→10 lifecycle', () => {
  test('Stage 0 blocks missing/unapproved/stale Project Contracts and accepts an explicit current approval', () => {
    withFixture((f) => {
      expect(validateProjectContract(f.contractPath, f.root).ok).toBe(false);

      writeJson(f.contractPath, contractFor(f, 'DRAFT'));
      const draft = validateProjectContract(f.contractPath, f.root);
      expect(draft.ok).toBe(false);
      expect(draft.approved).toBe(false);

      writeApprovedContract(f);
      const approved = validateProjectContract(f.contractPath, f.root);
      expect(approved.ok).toBe(true);
      expect(approved.approved).toBe(true);
      expect(approved.stale).toBe(false);

      writeFileSync(f.sourcePath, `${readFileSync(f.sourcePath, 'utf8')}changed\n`, 'utf8');
      const stale = validateProjectContract(f.contractPath, f.root);
      expect(stale.ok).toBe(false);
      expect(stale.stale).toBe(true);
      expect(stale.changedSources).toContain('docs/requirements.md');
    });
  });

  test('selects the real non-WordPress overlay and never imports WordPress implementation prohibitions', () => {
    withFixture((f) => {
      const contract = writeApprovedContract(f);
      expect(contract.tech_stack.wordpress).toBe(false);
      expect(contract.tech_stack.application_type).toBe('non-wordpress');

      const generic = readFileSync(
        join(GSTACK_ROOT, 'production-implement', 'references', 'non-wordpress-overlay.md'),
        'utf8',
      );
      const wordpress = readFileSync(
        join(GSTACK_ROOT, 'production-implement', 'references', 'wordpress-classic-overlay.md'),
        'utf8',
      );
      expect(generic).toContain('General / Non-WordPress Overlay');
      expect(generic).toContain('Apply the 75 controls and PREOS through the real stack');
      expect(generic).not.toContain('Gutenberg');
      expect(generic).not.toContain('permission_callback');
      expect(wordpress).toContain('classic theme');
      expect(wordpress).toContain('permission_callback');
    });
  });

  test('keeps the immutable 75-control minimum and augments it with bounded project-specific PREOS risks', () => {
    withFixture((f) => {
      writeApprovedContract(f);
      const coverage = writeControlCoverage(f);
      expect(validateCoverage(f.coveragePath)).toHaveLength(75);
      expect(coverage.map((r) => r.control_id)).toEqual(
        Array.from({ length: 75 }, (_, i) => `FS-${String(i + 1).padStart(3, '0')}`),
      );

      const risks = generateRiskSet({
        features: ['account-registration', 'profile-update'],
        multi_tenant: true,
        money_movement: false,
        files: false,
        queues: false,
        wordpress: false,
        maturity_stage: 1,
        threat_stage: 1,
      });
      expect(risks.length).toBeGreaterThan(0);
      expect(risks.every((r) => /^PREOS-(?:GEN|PAIR)-/.test(r.check_id))).toBe(true);
      expect(risks.some((r) => r.domain === 'Authorization and Tenant Isolation')).toBe(true);
      expect(risks.filter((r) => r.domain === 'Project-specific combinatorial risk')).toHaveLength(20);
      expect(risks.every((r) => r.gate_result === 'UNKNOWN')).toBe(true);
    });
  });

  test('Stage 5 remains blocked until contract, approved Stage-4 plan, 75 classifications, verified IU and fresh evidence all exist', () => {
    withFixture((f) => {
      writeApprovedContract(f);
      expect(stage5Preflight(f).ok).toBe(false);
      expect(stage5Preflight(f).reasons).toContain('approved Stage-4 plan missing');

      writeApprovedPlan(f);
      expect(stage5Preflight(f).ok).toBe(false);
      expect(stage5Preflight(f).reasons).toContain('75-control classification missing');

      writeControlCoverage(f);
      const risks = generateRiskSet({ features: ['account-registration'], multi_tenant: true });
      writeVerifiedImplementationUnit(f, risks);
      expect(stage5Preflight(f).ok).toBe(false);
      expect(stage5Preflight(f).reasons).toContain('evidence missing');

      writeFreshEvidence(f);
      expect(stage5Preflight(f)).toEqual({ ok: true, reasons: [] });
    });
  });

  test('walks the canonical external pipeline in exact 0→10 order with distinct lifecycle states and no Stage-5 self-approval', () => {
    withFixture((f) => {
      writeApprovedContract(f);
      writeControlCoverage(f);
      writeApprovedPlan(f);
      const risks = generateRiskSet({
        features: ['account-registration', 'profile-update'],
        multi_tenant: true,
        maturity_stage: 1,
        threat_stage: 1,
      });
      const iu = writeVerifiedImplementationUnit(f, risks);
      const evidence = writeFreshEvidence(f);
      expect(stage5Preflight(f)).toEqual({ ok: true, reasons: [] });
      expect(iu.status).toBe('VERIFIED');
      expect(evidenceFresh(evidence, new Date(), f.root).fresh).toBe(true);
      expect(evidence.config_version).toBe('fixture-config-v1');

      const docs = readFileSync(join(GSTACK_ROOT, 'docs', 'PREOS.md'), 'utf8');
      const documented = Array.from(docs.matchAll(/^\d+\. `([^`]+)`$/gm), (m) => m[1]);
      expect(documented).toEqual([...PIPELINE]);

      const ledger: Array<{ stage: number; skill: string; outcome: string }> = [];
      for (let stage = 0; stage < PIPELINE.length; stage++) {
        if (stage > 0) expect(ledger.at(-1)?.stage).toBe(stage - 1);
        if (stage === 5) expect(stage5Preflight(f).ok).toBe(true);
        if (stage === 6) expect(ledger.at(-1)?.outcome).toBe('IMPLEMENTATION COMPLETE');
        if (stage === 7) expect(ledger.at(-1)?.outcome).toBe('ENGINEERING REVIEW PASSED');
        if (stage === 8) expect(ledger.at(-1)?.outcome).toBe('QA PASSED');
        if (stage === 9) expect(ledger.at(-1)?.outcome).toBe('RELEASE READY');
        if (stage === 10) expect(ledger.at(-1)?.outcome).toBe('DEPLOYED');

        const row = { stage, skill: PIPELINE[stage], outcome: STAGE_OUTCOMES[stage] };
        ledger.push(row);
        writeState({
          status: 'VERIFIED',
          stage,
          skill: row.skill,
          lifecycle_status: row.outcome,
          next_unverified_action: stage < 10 ? `enter stage ${stage + 1} ${PIPELINE[stage + 1]}` : 'production feedback monitoring',
          pipeline_state: {
            current_stage: stage,
            current_skill: row.skill,
            completed_stages: ledger.map((x) => x.stage),
          },
        }, f.root);
      }

      expect(ledger.map((x) => x.stage)).toEqual(Array.from({ length: 11 }, (_, i) => i));
      expect(ledger.map((x) => x.skill)).toEqual([...PIPELINE]);
      expect(ledger[5].outcome).toBe('IMPLEMENTATION COMPLETE');
      expect(ledger[5].outcome).not.toBe('PRODUCTION APPROVED');
      expect(ledger[8].outcome).toBe('RELEASE READY');
      expect(ledger[9].outcome).toBe('DEPLOYED');
      expect(ledger[10].outcome).toBe('CANARY/PRODUCTION VERIFICATION PASSED');

      const completion = readFileSync(
        join(GSTACK_ROOT, 'production-implement', 'sections', 'completion.md.tmpl'),
        'utf8',
      );
      expect(completion).toContain('IMPLEMENTATION COMPLETE');
      expect(completion).toContain('Never emit `PRODUCTION APPROVED`');

      const stateDir = productionStateDir(f.root);
      const persisted = readFileSync(join(stateDir, 'implementation-ledger.jsonl'), 'utf8')
        .trim()
        .split(/\r?\n/)
        .map((line) => JSON.parse(line));
      expect(persisted).toHaveLength(11);
      expect(persisted.map((x) => x.stage)).toEqual(Array.from({ length: 11 }, (_, i) => i));
      expect(persisted.map((x) => x.skill)).toEqual([...PIPELINE]);

      const resume = reconcile(f.root);
      expect(resume.status).toBe('SAFE_TO_RESUME');
      expect(resume.resume_action).toBe('production feedback monitoring');
    });
  });
});
