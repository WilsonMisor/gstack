#!/usr/bin/env bun
import { readFileSync } from 'fs';
import { validateBaseline } from './validate-baseline-controls';

export const APPLICABILITY = ['Applies', 'Conditional', 'Not applicable', 'Escalate', 'Forbidden'] as const;
export type Applicability = typeof APPLICABILITY[number];

export function validateCoverage(path: string): any[] {
  const baseline = validateBaseline();
  const rows = JSON.parse(readFileSync(path, 'utf8')) as any[];
  if (!Array.isArray(rows)) throw new Error('coverage file must be a JSON array');
  const byNo = new Map<number, any>();
  for (const row of rows) {
    const no = Number(row.no ?? row.control_no);
    if (!Number.isInteger(no)) throw new Error('every coverage row needs numeric no/control_no');
    if (byNo.has(no)) throw new Error(`duplicate coverage for control ${no}`);
    if (!APPLICABILITY.includes(row.applicability)) throw new Error(`control ${no} has invalid/blank applicability: ${row.applicability}`);
    if (row.applicability === 'Not applicable' && !String(row.reason || '').trim()) throw new Error(`control ${no} Not applicable requires reason`);
    if (row.applicability === 'Conditional' && !String(row.condition || '').trim()) throw new Error(`control ${no} Conditional requires condition`);
    if (row.applicability === 'Escalate' && row.human_gate !== true) throw new Error(`control ${no} Escalate requires human_gate=true`);
    if (row.applicability === 'Forbidden' && row.approach_rejected !== true) throw new Error(`control ${no} Forbidden requires approach_rejected=true`);
    byNo.set(no, row);
  }
  for (const c of baseline) if (!byNo.has(c.no)) throw new Error(`missing applicability classification for control ${c.no}`);
  if (rows.length !== 75) throw new Error(`coverage must contain exactly 75 rows; got ${rows.length}`);
  return rows;
}

if (import.meta.main) {
  if (!process.argv[2]) throw new Error('usage: classify-control-coverage.ts <coverage.json>');
  const rows = validateCoverage(process.argv[2]);
  console.log(`CONTROL_COVERAGE_OK rows=${rows.length}`);
}
