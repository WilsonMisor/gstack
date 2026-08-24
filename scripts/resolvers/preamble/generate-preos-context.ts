import type { TemplateContext } from '../types';

const STAGE_GUIDANCE: Record<string, string> = {
  'office-hours': 'Stage 1: use the approved Project Contract while interrogating product pain, actors, outcomes, business model and assumptions.',
  'plan-ceo-review': 'Stage 2: challenge strategy, value, economics, failure modes and premature complexity; material scope expansion needs human approval.',
  'plan-eng-review': 'Stage 3: apply PREOS risk, change-impact, architecture, security, data, reliability, scaling, economics and evolution reasoning.',
  'autoplan': 'Stage 4: consolidate the approved lake into requirements, architecture, 75-control applicability, PREOS risks, deferred complexity, implementation units, tests/evidence and human gates; then hand off to /production-implement.',
  'production-implement': 'Stage 5: enforce the production-implement preflight; never bypass contract, approval, control, evidence or recovery gates.',
  'review': 'Stage 6: independently review the approved contract/plan, invariants, PREOS risks, controls and change impact.',
  'qa': 'Stage 7: independently exercise required behavioural, negative, adversarial, failure-path, permission/tenant and regression cases.',
  'ship': 'Stage 8: audit evidence freshness, critical gates, risk acceptance, migration/rollback/recovery, reconciliation and release readiness.',
  'land-and-deploy': 'Stage 9: keep deployment a distinct mutation boundary; respect human authority for irreversible production/data/infrastructure changes.',
  'canary': 'Stage 10: verify runtime invariants, reconciliation, reliability, security, performance, economics/cost and business signals; append learning.',
  'context-restore': 'Recovery: when PREOS state exists, reconcile machine state + Git and preserve pending approvals before Stage-5 edits.',
};

export function generatePreosContext(ctx: TemplateContext): string {
  const guidance = STAGE_GUIDANCE[ctx.skillName];
  if (!guidance) return '';
  return `## PREOS handoff\n\n${guidance}\n\nIf \`.gstack/project-contract/PROJECT-CONTRACT.json\` exists, read it first; detailed rules are in \`$GSTACK_ROOT/preos/references/stage-handoffs.md\`. Contract = application truth; this skill keeps its specialist role. Without a contract, preserve normal gstack unless full PREOS was requested. Never invent approval or map UNKNOWN to GREEN.`;
}
