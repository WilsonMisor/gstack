import { describe, expect, test } from 'bun:test';
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';
import { tmpdir } from 'os';
import { spawnSync } from 'child_process';
import { validateBaseline, EXPECTED_SEMANTIC_SHA256, semanticDigest } from '../../scripts/production-engine/validate-baseline-controls';
import { validateCoverage } from '../../scripts/production-engine/classify-control-coverage';
import { validateProjectContract } from '../../scripts/production-engine/validate-project-contract';
import { unsafeArchivePath } from '../../scripts/production-engine/safe-source-inventory';
import { generateRiskSet } from '../../scripts/production-engine/generate-risk-set';
import { validateDependencies } from '../../scripts/production-engine/validate-control-dependencies';
import { acceptanceValid, blockingCriticalRisks } from '../../scripts/production-engine/validate-risk-acceptance';
import { defenderCostAmplification, validateDeferredComplexity } from '../../scripts/production-engine/economics-complexity';
import { sha256File, writeJsonAtomic } from '../../scripts/production-engine/lib';

function temp(prefix='preos-') { return mkdtempSync(join(tmpdir(),prefix)); }
function coverage() { return Array.from({length:75},(_,i)=>({no:i+1,applicability:'Applies'})); }
function coveragePath(rows:any[]) { const p=join(temp(),'coverage.json'); writeFileSync(p,JSON.stringify(rows)); return p; }

describe('immutable deterministic baseline', () => {
  test('contains exactly original rows 1..75 with frozen semantic digest', () => {
    const controls=validateBaseline();
    expect(controls.map(c=>c.no)).toEqual(Array.from({length:75},(_,i)=>i+1));
    expect(semanticDigest(controls)).toBe(EXPECTED_SEMANTIC_SHA256);
  });
  test('requires all 75 applicability classifications and rejects blank/escalate without human gate/forbidden without rejection', () => {
    expect(validateCoverage(coveragePath(coverage()))).toHaveLength(75);
    let r=coverage(); r[0].applicability=''; expect(()=>validateCoverage(coveragePath(r))).toThrow();
    r=coverage(); (r[0] as any)={no:1,applicability:'Escalate'}; expect(()=>validateCoverage(coveragePath(r))).toThrow();
    (r[0] as any).human_gate=true; expect(validateCoverage(coveragePath(r))).toHaveLength(75);
    r=coverage(); (r[0] as any)={no:1,applicability:'Forbidden'}; expect(()=>validateCoverage(coveragePath(r))).toThrow();
  });
});

describe('Stage 0 source and contract safety', () => {
  test('archive traversal/absolute paths are blocked', () => {
    expect(unsafeArchivePath('../evil')).toBeTruthy();
    expect(unsafeArchivePath('/etc/passwd')).toBeTruthy();
    expect(unsafeArchivePath('C:/Windows/win.ini')).toBeTruthy();
    expect(unsafeArchivePath('docs/spec.md')).toBeNull();
  });
  test('source hash changes make approved contract stale', () => {
    const root=temp(); mkdirSync(join(root,'.gstack','project-contract'),{recursive:true});
    const src=join(root,'spec.txt'); writeFileSync(src,'v1');
    const contract=join(root,'.gstack','project-contract','PROJECT-CONTRACT.json');
    writeFileSync(contract,JSON.stringify({contract_id:'c1',version:'1',project_root:root,source_hashes:[{path:'spec.txt',sha256:sha256File(src)}],requirements:[],architecture:{},tech_stack:{},context:{},roles:{},authorities:{},approvals:[{status:'APPROVED',authority:'PDM',timestamp:new Date().toISOString()}],status:'APPROVED'}));
    expect(validateProjectContract(contract,root).ok).toBe(true);
    writeFileSync(src,'v2');
    expect(validateProjectContract(contract,root).stale).toBe(true);
  });
});

describe('PREOS risk, economics and evidence rules', () => {
  test('risk generator uses all 52-domain seed set selectively and bounded pairwise context', () => {
    const risks=generateRiskSet({features:['withdrawal'],money_movement:true,multi_tenant:true,maturity_stage:1,threat_stage:2});
    expect(risks.some(r=>r.domain==='Money and Financial Correctness')).toBe(true);
    expect(risks.some(r=>r.domain==='Economic Abuse Surface')).toBe(true);
    expect(risks.some(r=>r.domain==='Authorization and Tenant Isolation')).toBe(true);
    expect(risks.filter(r=>r.domain==='Project-specific combinatorial risk')).toHaveLength(10);
    expect(risks.every(r=>r.gate_result==='UNKNOWN')).toBe(true);
  });
  test('GREEN cannot depend on UNKNOWN/RED/HUMAN REVIEW', () => {
    const rows:any[]=[{check_id:'A',gate_result:'UNKNOWN',control_dependencies:[]},{check_id:'B',gate_result:'GREEN',control_dependencies:['A']}];
    expect(validateDependencies(rows)).toHaveLength(1); rows[0].gate_result='GREEN'; expect(validateDependencies(rows)).toEqual([]);
  });
  test('risk acceptance is explicit and expiring', () => {
    const a={risk_id:'R1',authority:'SEC',reason:'temporary',scope:'release-1',timestamp:new Date().toISOString(),expiration:new Date(Date.now()+86400000).toISOString(),status:'APPROVED'};
    expect(acceptanceValid(a)).toBe(true);
    expect(blockingCriticalRisks([{check_id:'R1',severity:'CRITICAL',gate_result:'RED'}],[a])).toEqual([]);
    expect(acceptanceValid({...a,expiration:'2020-01-01'})).toBe(false);
  });
  test('deferred complexity needs measurable trigger/migration and economic abuse is detectable', () => {
    const d:any={item:'Kafka',concrete_problem:'none yet',needed_now:false,simple_solution:'DB outbox',complex_solution:'Kafka',operational_burden:'specialist ops',new_failure_modes:['broker outage']};
    expect(validateDeferredComplexity(d)).toContain('measurable activation trigger required');
    d.activation_trigger='sustained 50k events/min'; d.migration_path='outbox -> broker'; expect(validateDeferredComplexity(d)).toEqual([]);
    expect(defenderCostAmplification(.01,1).amplified).toBe(true);
  });
});

describe('authority, pipeline and stage boundaries', () => {
  const root=resolve(import.meta.dir,'../..');
  test('canonical external pipeline remains Stage 0-10 without extra mandatory PREOS stages', () => {
    const s=readFileSync(join(root,'docs','PREOS.md'),'utf8');
    for(const name of ['$project-init','$office-hours','$plan-ceo-review','$plan-eng-review','$autoplan','$production-implement','$review','$qa','$ship','$land-and-deploy','$canary']) expect(s).toContain(name);
    expect(s).toContain('not additional mandatory user-facing stages');
  });
  test('project-init cannot write application code and Stage 5 cannot self-approve production', () => {
    expect(readFileSync(join(root,'project-init','SKILL.md.tmpl'),'utf8')).toContain('No application-code mutation');
    const c=readFileSync(join(root,'production-implement','sections','completion.md.tmpl'),'utf8');
    expect(c).toContain('IMPLEMENTATION COMPLETE'); expect(c).toContain('Never emit `PRODUCTION APPROVED`');
  });
  test('domain skills remain independent and WordPress rules stay overlay-specific', () => {
    expect(readFileSync(join(root,'project-init','references','domain-skill-interoperability.md'),'utf8')).toContain('never copy or overwrite');
    const wp=readFileSync(join(root,'production-implement','references','wordpress-classic-overlay.md'),'utf8');
    const generic=readFileSync(join(root,'production-implement','references','non-wordpress-overlay.md'),'utf8');
    expect(wp).toContain('classic theme'); expect(wp).toContain('permission_callback'); expect(generic).not.toContain('Gutenberg');
  });
});
