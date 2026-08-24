#!/usr/bin/env bun
import { existsSync, readFileSync } from 'fs';
import { dirname, isAbsolute, join, resolve } from 'path';
import { sha256File } from './lib';

export interface ContractValidation {
  ok: boolean;
  stale: boolean;
  approved: boolean;
  errors: string[];
  changedSources: string[];
}

function normalizeHashEntries(sourceHashes: any): Array<{ path: string; sha256: string }> {
  if (Array.isArray(sourceHashes)) return sourceHashes.map((x) => ({ path: String(x.path), sha256: String(x.sha256) }));
  if (sourceHashes && typeof sourceHashes === 'object') return Object.entries(sourceHashes).map(([path, sha256]) => ({ path, sha256: String(sha256) }));
  return [];
}

export function validateProjectContract(contractPath: string, projectRoot?: string): ContractValidation {
  const errors: string[] = [];
  const changedSources: string[] = [];
  if (!existsSync(contractPath)) return { ok: false, stale: false, approved: false, errors: ['Project Contract does not exist'], changedSources };
  const contract = JSON.parse(readFileSync(contractPath, 'utf8')) as any;
  for (const key of ['contract_id', 'version', 'source_hashes', 'requirements', 'architecture', 'tech_stack', 'approvals', 'status']) {
    if (contract[key] == null || contract[key] === '') errors.push(`missing ${key}`);
  }
  const root = resolve(projectRoot || contract.project_root || join(dirname(contractPath), '..', '..'));
  for (const e of normalizeHashEntries(contract.source_hashes)) {
    const p = isAbsolute(e.path) ? e.path : resolve(root, e.path);
    if (!existsSync(p)) { changedSources.push(e.path); continue; }
    if (sha256File(p) !== e.sha256) changedSources.push(e.path);
  }
  const unresolved = contract.unresolved_conflicts ?? contract.source_conflicts ?? [];
  if (Array.isArray(unresolved) && unresolved.some((c: any) => !c || c.status == null || !['RESOLVED','SUPERSEDED','NOT_APPLICABLE'].includes(String(c.status)))) {
    errors.push('Project Contract has unresolved material source conflicts');
  }
  if (contract.blocked === true || contract.status === 'BLOCKED') errors.push('Project Contract is BLOCKED');
  const approved = contract.status === 'APPROVED' && Array.isArray(contract.approvals)
    ? contract.approvals.some((a: any) => a && a.status === 'APPROVED' && a.authority && a.timestamp)
    : contract.status === 'APPROVED' && !!contract.approvals;
  const stale = changedSources.length > 0 || contract.status === 'STALE';
  if (stale) errors.push(`Project Contract is STALE (${changedSources.length} source changes)`);
  if (!approved) errors.push('Project Contract is not explicitly approved');
  return { ok: errors.length === 0, stale, approved, errors, changedSources };
}

if (import.meta.main) {
  const p = process.argv[2];
  if (!p) throw new Error('usage: validate-project-contract.ts <PROJECT-CONTRACT.json> [project-root]');
  const result = validateProjectContract(resolve(p), process.argv[3]);
  console.log(JSON.stringify(result, null, 2));
  if (!result.ok) process.exit(2);
}
