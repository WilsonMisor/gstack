#!/usr/bin/env bun
import { join } from 'path';
import { appendJsonl, branchName, headSha, isoNow, productionStateDir, workingTreeFingerprint, writeJsonAtomic } from './lib';

export type PipelineStatus = 'READY'|'IMPLEMENTING'|'VERIFYING'|'VERIFIED'|'BLOCKED'|'RECOVERY_CONFLICT';

export function writeState(event: any, cwd = process.cwd()): any {
  const dir = productionStateDir(cwd);
  const snapshot = {
    ...event,
    timestamp: isoNow(),
    branch: branchName(cwd),
    head_sha: headSha(cwd),
    working_tree_fingerprint: workingTreeFingerprint(cwd),
  };
  writeJsonAtomic(join(dir, 'CURRENT-STATE.json'), snapshot);
  appendJsonl(join(dir, 'implementation-ledger.jsonl'), snapshot);
  if (event.pipeline_state) writeJsonAtomic(join(dir, 'PIPELINE-STATE.json'), event.pipeline_state);
  if (event.approval_state) writeJsonAtomic(join(dir, 'approval-state.json'), event.approval_state);
  return snapshot;
}

if (import.meta.main) {
  const json = process.argv[2];
  if (!json) throw new Error("usage: state-write.ts '<json-event>'");
  console.log(JSON.stringify(writeState(JSON.parse(json)), null, 2));
}
