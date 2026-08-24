#!/usr/bin/env bun
import { join } from 'path';
import { appendJsonl, isoNow, productionStateDir } from './lib';

export function appendIncidentLearning(input: any, cwd = process.cwd()): any {
  for (const key of ['incident_id','root_cause','trigger','why_risk_system_missed_it']) {
    if (!String(input[key] || '').trim()) throw new Error(`${key} is required`);
  }
  const record = {
    ...input,
    timestamp: input.timestamp || isoNow(),
    append_only: true,
    required_updates: {
      atomic_risk_rule: input.atomic_risk_rule || null,
      regression_test: input.regression_test || null,
      monitoring: input.monitoring || null,
      runbook: input.runbook || null,
      architecture_review_trigger: input.architecture_review_trigger || null,
      cost_model: input.cost_model || null,
      security_model: input.security_model || null,
    },
  };
  appendJsonl(join(productionStateDir(cwd), 'incident-learning.jsonl'), record);
  return record;
}

if (import.meta.main) {
  const raw = process.argv[2];
  if (!raw) throw new Error("usage: incident-learn.ts '<json>'");
  console.log(JSON.stringify(appendIncidentLearning(JSON.parse(raw)), null, 2));
}
