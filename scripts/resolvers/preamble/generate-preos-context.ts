import type { TemplateContext } from '../types';

const STAGE_GUIDANCE: Record<string, string> = {
  'office-hours': 'Stage 1: product interrogation.',
  'plan-ceo-review': 'Stage 2: strategy, economics and scope.',
  'plan-eng-review': 'Stage 3: architecture, risk and change impact.',
  'autoplan': 'Stage 4: approved-lake plan and human gates; then /production-implement.',
  'production-implement': 'Stage 5: implementation under contract, controls, evidence and recovery gates.',
  'review': 'Stage 6: independent engineering review.',
  'qa': 'Stage 7: independent behavioural and failure-path QA.',
  'ship': 'Stage 8: release and evidence readiness.',
  'land-and-deploy': 'Stage 9: controlled deployment boundary.',
  'canary': 'Stage 10: runtime verification and append-only learning.',
  'context-restore': 'Recovery: reconcile PREOS state + Git; preserve pending approvals.',
};

export function generatePreosContext(ctx: TemplateContext): string {
  const guidance = STAGE_GUIDANCE[ctx.skillName];
  if (!guidance) return '';
  return `**PREOS:** ${guidance}\n\n\`.gstack/project-contract/PROJECT-CONTRACT.json\` present: read it + \`preos/references/stage-handoffs.md\`; contract=app truth, skill=procedure. Else normal gstack unless PREOS requested. Never invent approval; UNKNOWN≠GREEN.`;
}
