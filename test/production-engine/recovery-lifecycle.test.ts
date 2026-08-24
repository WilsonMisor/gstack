import { describe, expect, test } from 'bun:test';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { writeState } from '../../scripts/production-engine/state-write';
import { reconcile } from '../../scripts/production-engine/state-reconcile';
import { headSha, productionStateDir } from '../../scripts/production-engine/lib';

const GSTACK_ROOT = resolve(import.meta.dir, '../..');

type Fixture = {
  root: string;
  stateRoot: string;
  trackedPath: string;
};

function git(cwd: string, args: string[]): string {
  const r = spawnSync('git', args, { cwd, encoding: 'utf8', timeout: 30_000 });
  if (r.status !== 0) throw new Error(`git ${args.join(' ')} failed: ${r.stderr || r.stdout}`);
  return String(r.stdout || '').trim();
}

function newFixture(): Fixture {
  const root = mkdtempSync(join(tmpdir(), 'preos-recovery-app-'));
  const stateRoot = mkdtempSync(join(tmpdir(), 'preos-recovery-state-'));
  git(root, ['init']);
  git(root, ['checkout', '-b', 'fixture/recovery']);
  git(root, ['config', 'user.email', 'fixture@example.invalid']);
  git(root, ['config', 'user.name', 'PREOS Recovery Fixture']);
  const trackedPath = join(root, 'service.txt');
  writeFileSync(trackedPath, 'v1\n', 'utf8');
  git(root, ['add', '.']);
  git(root, ['commit', '-m', 'fixture: initial recovery state']);
  return { root, stateRoot, trackedPath };
}

function withFixture(fn: (f: Fixture) => void): void {
  const oldStateRoot = process.env.GSTACK_STATE_ROOT;
  const f = newFixture();
  process.env.GSTACK_STATE_ROOT = f.stateRoot;
  try {
    fn(f);
  } finally {
    if (oldStateRoot === undefined) delete process.env.GSTACK_STATE_ROOT;
    else process.env.GSTACK_STATE_ROOT = oldStateRoot;
    rmSync(f.root, { recursive: true, force: true });
    rmSync(f.stateRoot, { recursive: true, force: true });
  }
}

describe('PREOS crash and recovery acceptance', () => {
  test('AT-018 — crash with pending human approval preserves PENDING and never infers approval', () => {
    withFixture((f) => {
      writeState({
        status: 'BLOCKED',
        stage: 5,
        current_iu: 'IU-SEC-001',
        next_unverified_action: 'await security approval before authz change',
        approval_state: {
          approval_id: 'APP-SEC-001',
          status: 'PENDING',
          authority: 'SEC',
          scope: 'authorization boundary change',
        },
      }, f.root);

      const result = reconcile(f.root);
      expect(result.status).toBe('PENDING_APPROVAL');
      expect(result.reasons.join(' ')).toContain('human approval remains pending');
      expect(result.state?.current_iu).toBe('IU-SEC-001');

      const approval = JSON.parse(readFileSync(join(productionStateDir(f.root), 'approval-state.json'), 'utf8'));
      expect(approval.status).toBe('PENDING');
      expect(approval.status).not.toBe('APPROVED');
    });
  });

  test('AT-019 — crash mid-IU resumes at the recorded first unverified action', () => {
    withFixture((f) => {
      const action = 're-run first uncertain verification for IU-002: tenant isolation failure test';
      writeState({
        status: 'VERIFYING',
        stage: 5,
        current_iu: 'IU-002',
        last_verified_action: 'unit and contract tests passed',
        next_unverified_action: action,
        pipeline_state: {
          current_stage: 5,
          current_skill: '$production-implement',
          current_iu: 'IU-002',
        },
      }, f.root);

      const result = reconcile(f.root);
      expect(result.status).toBe('SAFE_TO_RESUME');
      expect(result.resume_action).toBe(action);
      expect(result.state?.current_iu).toBe('IU-002');
      expect(result.state?.last_verified_action).toBe('unit and contract tests passed');
    });
  });

  test('AT-020 — Git/worktree disagreement becomes RECOVERY_CONFLICT instead of silent resume', () => {
    withFixture((f) => {
      writeState({
        status: 'IMPLEMENTING',
        stage: 5,
        current_iu: 'IU-003',
        next_unverified_action: 'verify current implementation diff',
      }, f.root);

      writeFileSync(f.trackedPath, 'v2-after-crash\n', 'utf8');
      const result = reconcile(f.root);
      expect(result.status).toBe('RECOVERY_CONFLICT');
      expect(result.reasons.join(' ')).toContain('working tree differs from recorded in-progress state');
    });
  });

  test('AT-034 — “start from the last session” routes to restore and a fresh process resumes from persistent state + Git', () => {
    withFixture((f) => {
      const router = readFileSync(join(GSTACK_ROOT, 'SKILL.md.tmpl'), 'utf8');
      expect(router).toContain('start from the last session');
      expect(router).toContain('invoke `/context-restore`');
      expect(router).toContain('reconcile persistent state + Git before edits');

      const action = 're-run first uncertain verification: recovery-path regression test';
      const saved = writeState({
        status: 'VERIFYING',
        stage: 5,
        current_iu: 'IU-RECOVERY-004',
        last_verified_action: 'rollback plan verified',
        next_unverified_action: action,
        pipeline_state: {
          current_stage: 5,
          current_skill: '$production-implement',
          current_iu: 'IU-RECOVERY-004',
          completed_stages: [0, 1, 2, 3, 4],
        },
      }, f.root);

      const dir = productionStateDir(f.root);
      expect(existsSync(join(dir, 'CURRENT-STATE.json'))).toBe(true);
      expect(existsSync(join(dir, 'PIPELINE-STATE.json'))).toBe(true);
      expect(existsSync(join(dir, 'implementation-ledger.jsonl'))).toBe(true);
      expect(saved.head_sha).toBe(headSha(f.root));

      const child = spawnSync(
        process.execPath,
        [join(GSTACK_ROOT, 'scripts', 'production-engine', 'state-reconcile.ts')],
        {
          cwd: f.root,
          encoding: 'utf8',
          timeout: 30_000,
          env: { ...process.env, GSTACK_STATE_ROOT: f.stateRoot },
        },
      );
      expect(child.status).toBe(0);
      const restored = JSON.parse(String(child.stdout || '{}'));
      expect(restored.status).toBe('SAFE_TO_RESUME');
      expect(restored.resume_action).toBe(action);
      expect(restored.state.current_iu).toBe('IU-RECOVERY-004');
      expect(restored.state.last_verified_action).toBe('rollback plan verified');
      expect(restored.state.branch).toBe('fixture/recovery');
      expect(restored.state.head_sha).toBe(headSha(f.root));
    });
  }, 20_000);
});
