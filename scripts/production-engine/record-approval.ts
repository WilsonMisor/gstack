#!/usr/bin/env bun
import { join } from 'path';
import { appendJsonl, isoNow, productionStateDir, writeJsonAtomic } from './lib';

const APPROVABLE = new Set(['APPROVED','REJECTED','PENDING']);

export function recordApproval(input: any, cwd = process.cwd()): any {
  if (!input.approval_id || !input.decision || !input.authority) throw new Error('approval_id, decision and authority are required');
  const status = input.status || 'PENDING';
  if (!APPROVABLE.has(status)) throw new Error(`invalid approval status: ${status}`);
  const record = { ...input, status, timestamp: input.timestamp || isoNow() };
  const dir = productionStateDir(cwd);
  appendJsonl(join(dir, 'approval-events.jsonl'), record);
  writeJsonAtomic(join(dir, 'approval-state.json'), record);
  return record;
}

if (import.meta.main) {
  const raw = process.argv[2];
  if (!raw) throw new Error("usage: record-approval.ts '<json>'");
  console.log(JSON.stringify(recordApproval(JSON.parse(raw)), null, 2));
}
