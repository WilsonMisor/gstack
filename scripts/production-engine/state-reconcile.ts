#!/usr/bin/env bun
import { existsSync, readFileSync } from 'fs';
import { join } from 'path';
import { branchName, headSha, productionStateDir, workingTreeFingerprint } from './lib';

export interface ReconcileResult {
  status: 'NO_STATE'|'SAFE_TO_RESUME'|'RECOVERY_CONFLICT'|'PENDING_APPROVAL';
  resume_action?: string;
  reasons: string[];
  state?: any;
}

export function reconcile(cwd = process.cwd()): ReconcileResult {
  const dir = productionStateDir(cwd);
  const statePath = join(dir, 'CURRENT-STATE.json');
  if (!existsSync(statePath)) return { status: 'NO_STATE', reasons: ['no production CURRENT-STATE.json'] };
  const state = JSON.parse(readFileSync(statePath,'utf8'));
  const reasons: string[] = [];
  if (state.branch && state.branch !== branchName(cwd)) reasons.push(`branch differs: recorded=${state.branch} current=${branchName(cwd)}`);
  const currentHead = headSha(cwd);
  if (state.safe_head_sha && currentHead !== state.safe_head_sha && currentHead !== state.head_sha) reasons.push('HEAD differs from recorded safe state');
  const fp = workingTreeFingerprint(cwd);
  if (state.working_tree_fingerprint && fp !== state.working_tree_fingerprint && state.status !== 'VERIFIED') reasons.push('working tree differs from recorded in-progress state');
  // Git/filesystem disagreement dominates: a pending approval stays pending in the ledger,
  // but we must not hide an independent recovery conflict behind it.
  if (reasons.length) return { status: 'RECOVERY_CONFLICT', reasons, state };
  const approvalPath = join(dir, 'approval-state.json');
  if (existsSync(approvalPath)) {
    const approval = JSON.parse(readFileSync(approvalPath,'utf8'));
    if (approval.status === 'PENDING') return { status: 'PENDING_APPROVAL', reasons: ['human approval remains pending; never infer approval'], state };
  }
  return { status: 'SAFE_TO_RESUME', resume_action: state.next_unverified_action || 're-run verification for current implementation unit', reasons: [], state };
}

if (import.meta.main) {
  const result = reconcile();
  console.log(JSON.stringify(result, null, 2));
  if (result.status === 'RECOVERY_CONFLICT') process.exit(2);
  if (result.status === 'PENDING_APPROVAL') process.exit(3);
}
