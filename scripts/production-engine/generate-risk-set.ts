#!/usr/bin/env bun
import { readFileSync } from 'fs';
import { resolve } from 'path';

export interface RiskContext {
  features?: string[];
  domains?: string[];
  actors?: string[];
  money_movement?: boolean;
  multi_tenant?: boolean;
  ai?: boolean;
  files?: boolean;
  queues?: boolean;
  mobile?: boolean;
  wordpress?: boolean;
  maturity_stage?: number;
  threat_stage?: number;
}

const HIGH_COUPLING = ['retry','concurrency','permission','dependency','money','tenant','time','configuration','recovery','cost'];

export function generateRiskSet(context: RiskContext, cataloguePath?: string): any[] {
  const cat = cataloguePath
    ? JSON.parse(readFileSync(cataloguePath, 'utf8')) as { domains: Array<{ domain: string; features: string[] }> }
    : { domains: [1,2,3,4].flatMap((part) => {
        const p = resolve(import.meta.dir, `../../preos/catalogues/risk-features.part-${part}.json`);
        return (JSON.parse(readFileSync(p, 'utf8')) as { domains: Array<{ domain: string; features: string[] }> }).domains;
      }) };
  const wantedDomains = new Set(context.domains || []);
  const always = new Set([
    'Product and Business Rules','Data Semantics and Data Types','Database Design','API Engineering','Security',
    'Privacy and Data Lifecycle','CI, CD, and Version Control','Observability','Reliability and Availability',
    'Backup, Recovery, and Disaster Recovery','Human Error and Insider Risk','Support and Operations',
    'Configuration and Feature-State Engineering','Change Impact Engineering','Evidence Freshness and Validity',
    'Control Dependency Graph','Human Authority and Decision Rights','AI Coding Agent Authority Boundary',
  ]);
  if (context.money_movement) ['Money and Financial Correctness','Billing and Subscription','Trade Assurance and Protected Transactions','Economic Abuse Surface'].forEach((d) => always.add(d));
  if (context.multi_tenant) always.add('Authorization and Tenant Isolation');
  if (context.ai) always.add('AI Specific Risks');
  if (context.files) always.add('Files and Object Storage');
  if (context.queues) always.add('Queues, Events, and Background Work');
  if (context.mobile) always.add('Mobile Engineering');
  for (const d of wantedDomains) always.add(d);

  const materialized: any[] = [];
  let seq = 1;
  for (const d of cat.domains) {
    if (!always.has(d.domain)) continue;
    for (const feature of d.features) {
      materialized.push({
        check_id: `PREOS-GEN-${String(seq++).padStart(4,'0')}`,
        domain: d.domain,
        feature,
        source_category: 'catalogue-seed',
        current_status: 'UNKNOWN',
        gate_result: 'UNKNOWN',
        generated_dimensions: ['single-fault', ...HIGH_COUPLING.slice(0, 3)],
        production_maturity_stage: context.maturity_stage ?? 1,
        threat_stage: context.threat_stage ?? 0,
      });
    }
  }
  for (const feature of context.features || []) {
    for (const dimension of HIGH_COUPLING) {
      materialized.push({
        check_id: `PREOS-PAIR-${String(seq++).padStart(4,'0')}`,
        domain: 'Project-specific combinatorial risk',
        feature,
        dimension,
        failure_scenario: `${feature} under adverse ${dimension} conditions`,
        current_status: 'UNKNOWN',
        gate_result: 'UNKNOWN',
        source_category: 'context-generated',
      });
    }
  }
  return materialized;
}

if (import.meta.main) {
  const path = process.argv[2];
  if (!path) throw new Error('usage: generate-risk-set.ts <context.json>');
  const context = JSON.parse(readFileSync(path, 'utf8')) as RiskContext;
  console.log(JSON.stringify(generateRiskSet(context), null, 2));
}
