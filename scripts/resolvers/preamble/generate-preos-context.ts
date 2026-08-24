import type { TemplateContext } from '../types';

const STAGE_GUIDANCE: Record<string, string> = {
  'office-hours': 'Stage 1: use the Project Contract as application truth while interrogating product pain, actors, outcomes, business model, critical workflows and assumptions. Do not silently contradict approved source decisions.',
  'plan-ceo-review': 'Stage 2: challenge strategic scope, value, business failure modes, revenue/unit economics and premature complexity. Expansion outside the approved lake is a human decision.',
  'plan-eng-review': 'Stage 3: apply PREOS risk generation, change impact, reliability/security/data/concurrency/economics/scaling/evolution reasoning. Record simpler alternatives and measurable complexity triggers.',
  'autoplan': 'Stage 4: consolidate requirements, architecture decisions, 75-control applicability, PREOS risks, deferred complexity, implementation units, tests/evidence and final human approvals. Completeness means boil the approved lake, not silent scope expansion. For PREOS application work, after the Stage-4 plan and material human gates are approved, the next implementation step is `/production-implement`; do not skip directly to `/ship`.',
  'production-implement': 'Stage 5: the production-implement skill owns the hard contract/plan/control/risk/evidence/recovery gates. Never bypass its preflight.',
  'review': 'Stage 6: independently review the branch against the approved Project Contract/plan, invariants, PREOS risks, 75 controls and change impact. Do not treat Stage-5 self-verification as independent review.',
  'qa': 'Stage 7: independently exercise behavioural, negative, adversarial, failure-path, permission/cross-tenant and regression cases required by the Project Contract/PREOS risk set.',
  'ship': 'Stage 8: audit evidence freshness/completeness, critical gate status, authorized risk acceptance, migrations, rollback/recovery, reconciliation, operations and release readiness. Critical RED/UNKNOWN/HUMAN REVIEW cannot be hidden by aggregate status.',
  'land-and-deploy': 'Stage 9: deployment remains a distinct mutation boundary. Respect human authority for irreversible production/data/infrastructure changes and preserve rollback/recovery evidence.',
  'canary': 'Stage 10: verify runtime invariants, reconciliation, reliability, security, performance, economic/cost and business signals. Production findings feed append-only PREOS learning rather than rewriting history.',
  'context-restore': 'Recovery handoff: after human-readable context restore, if PREOS production state exists, reconcile machine state + Git and preserve pending approvals before any Stage-5 edits.',
};

export function generatePreosContext(ctx: TemplateContext): string {
  const guidance = STAGE_GUIDANCE[ctx.skillName];
  if (!guidance) return '';
  return `## PREOS Project Contract handoff\n\n${guidance}\n\nWhen this repository has \`.gstack/project-contract/PROJECT-CONTRACT.json\`, Read it before making project-specific decisions in this stage. Also consult \`$GSTACK_ROOT/preos/references/stage-handoffs.md\` when available. The Project Contract is application truth; PREOS is production governance; the current gstack skill keeps its specialist responsibility.\n\nIf no Project Contract exists, preserve ordinary gstack behavior unless the user explicitly asked for the full PREOS Stage 0-10 pipeline. Never invent approval or silently make UNKNOWN production state GREEN.`;
}
