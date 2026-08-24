#!/usr/bin/env bun
import { existsSync, readFileSync } from 'fs';
import { headSha, workingTreeFingerprint } from './lib';

export function evidenceFresh(e: any, now = new Date(), cwd = process.cwd()): { fresh: boolean; reason?: string } {
  if (!e || e.status !== 'PASS') return { fresh: false, reason: 'evidence missing or not PASS' };
  if (!e.produced_at || !e.environment || !e.commit_sha) return { fresh: false, reason: 'evidence missing produced_at/environment/commit_sha' };
  if (e.expires_at && new Date(e.expires_at).getTime() <= now.getTime()) return { fresh: false, reason: 'evidence expired' };
  const head = headSha(cwd);
  if (head && e.commit_sha !== head && !e.working_tree_fingerprint) return { fresh: false, reason: 'commit changed and no working-tree fingerprint binding' };
  if (e.working_tree_fingerprint && e.working_tree_fingerprint !== workingTreeFingerprint(cwd)) return { fresh: false, reason: 'working tree changed' };
  if (e.log_path && !existsSync(e.log_path)) return { fresh: false, reason: 'referenced evidence log missing' };
  if (e.invalidation_triggered === true) return { fresh: false, reason: 'evidence invalidation trigger fired' };
  return { fresh: true };
}

if (import.meta.main) {
  const p = process.argv[2];
  if (!p) throw new Error('usage: validate-preos-evidence.ts <evidence.json>');
  const records = JSON.parse(readFileSync(p,'utf8')) as any[];
  const results = records.map((e) => ({ id: e.evidence_id, ...evidenceFresh(e) }));
  console.log(JSON.stringify(results, null, 2));
  if (results.some((r) => !r.fresh)) process.exit(2);
}
