#!/usr/bin/env bun
import { readFileSync } from 'fs';

const NON_GREEN = new Set(['RED','UNKNOWN','HUMAN REVIEW']);

export function validateDependencies(records: any[]): string[] {
  const byId = new Map(records.map((r) => [String(r.check_id || r.control_id), r]));
  const errors: string[] = [];
  for (const r of records) {
    if (r.gate_result !== 'GREEN') continue;
    for (const dep of r.control_dependencies || []) {
      const d = byId.get(String(dep));
      if (!d) errors.push(`${r.check_id || r.control_id} is GREEN but dependency ${dep} is missing`);
      else if (NON_GREEN.has(d.gate_result)) errors.push(`${r.check_id || r.control_id} is GREEN but dependency ${dep} is ${d.gate_result}`);
    }
  }
  return errors;
}

if (import.meta.main) {
  const p = process.argv[2];
  if (!p) throw new Error('usage: validate-control-dependencies.ts <records.json>');
  const records = JSON.parse(readFileSync(p,'utf8'));
  const errors = validateDependencies(records);
  console.log(JSON.stringify({ ok: errors.length === 0, errors }, null, 2));
  if (errors.length) process.exit(2);
}
