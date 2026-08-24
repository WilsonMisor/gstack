#!/usr/bin/env bun
import { readFileSync } from 'fs';

export function acceptanceValid(a: any, now = new Date()): boolean {
  if (!a || a.status !== 'APPROVED' || !a.risk_id || !a.authority || !a.reason || !a.scope || !a.timestamp) return false;
  if (!a.expiration) return false;
  const exp = new Date(a.expiration);
  return Number.isFinite(exp.getTime()) && exp.getTime() > now.getTime();
}

export function blockingCriticalRisks(risks: any[], acceptances: any[], now = new Date()): string[] {
  const valid = new Set(acceptances.filter((a) => acceptanceValid(a, now)).map((a) => String(a.risk_id)));
  return risks
    .filter((r) => (r.severity === 'CRITICAL' || r.severity === 'HIGH') && r.gate_result === 'RED' && !valid.has(String(r.check_id)))
    .map((r) => String(r.check_id));
}

if (import.meta.main) {
  const [risksPath, acceptancePath] = process.argv.slice(2);
  if (!risksPath || !acceptancePath) throw new Error('usage: validate-risk-acceptance.ts <risks.json> <acceptances.json>');
  const blocked = blockingCriticalRisks(JSON.parse(readFileSync(risksPath,'utf8')), JSON.parse(readFileSync(acceptancePath,'utf8')));
  console.log(JSON.stringify({ ok: blocked.length === 0, blocked }, null, 2));
  if (blocked.length) process.exit(2);
}
