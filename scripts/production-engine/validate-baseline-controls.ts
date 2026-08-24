#!/usr/bin/env bun
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { createHash } from 'crypto';

export const EXPECTED_SEMANTIC_SHA256 = '5bbef39af88e0162c39db5b80ad2a86d70b3f50083196ac0001e8171b24dd617';

export interface BaselineControl {
  no: number;
  gate_and_acceptance_condition: string;
  applicability_rule: string;
  required_test: string;
  evidence_before_acceptance: string;
  source: string;
}

export function semanticDigest(controls: BaselineControl[]): string {
  const canonical = JSON.stringify(controls.map((c) => ({
    applicability_rule: c.applicability_rule,
    evidence_before_acceptance: c.evidence_before_acceptance,
    gate_and_acceptance_condition: c.gate_and_acceptance_condition,
    no: c.no,
    required_test: c.required_test,
    source: c.source,
  })));
  return createHash('sha256').update(canonical).digest('hex');
}

export function validateBaseline(path?: string): BaselineControl[] {
  let controls: BaselineControl[];
  if (path) {
    const parsed = JSON.parse(readFileSync(path, 'utf8')) as { count?: number; controls: BaselineControl[] };
    controls = parsed.controls || [];
  } else {
    const base = resolve(import.meta.dir, '../../preos/baseline');
    controls = [1, 2, 3].flatMap((part) => {
      const parsed = JSON.parse(readFileSync(resolve(base, `controls-75.part-${part}.json`), 'utf8')) as { controls: BaselineControl[] };
      return parsed.controls || [];
    });
  }
  if (controls.length !== 75) throw new Error(`expected exactly 75 controls, found rows=${controls.length}`);
  const seen = new Set<number>();
  const required = ['gate_and_acceptance_condition', 'applicability_rule', 'required_test', 'evidence_before_acceptance', 'source'] as const;
  for (const c of controls) {
    if (!Number.isInteger(c.no) || c.no < 1 || c.no > 75) throw new Error(`invalid control number: ${c.no}`);
    if (seen.has(c.no)) throw new Error(`duplicate control number: ${c.no}`);
    seen.add(c.no);
    for (const key of required) if (typeof c[key] !== 'string' || !c[key].trim()) throw new Error(`control ${c.no} missing ${key}`);
  }
  for (let i = 1; i <= 75; i++) if (!seen.has(i)) throw new Error(`missing control ${i}`);
  const digest = semanticDigest(controls);
  if (digest !== EXPECTED_SEMANTIC_SHA256) throw new Error(`baseline semantic digest changed: expected ${EXPECTED_SEMANTIC_SHA256}, got ${digest}`);
  return controls;
}

if (import.meta.main) {
  const controls = validateBaseline(process.argv[2]);
  console.log(`BASELINE_OK count=${controls.length} sha256=${EXPECTED_SEMANTIC_SHA256}`);
}
