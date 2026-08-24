/**
 * Preamble composition root.
 *
 * Each generator lives in its own file under ./preamble/*.ts. This file only
 * wires them together via generatePreamble(). Keep composition declarative —
 * no inline logic beyond tier gating.
 *
 * Each skill runs independently via `claude -p` (or the host's equivalent).
 * There is no shared loader. The preamble provides: update checks, session
 * tracking, user preferences, repo mode detection, model overlays, and
 * telemetry.
 */

import type { TemplateContext } from './types';
import { generateModelOverlay } from './model-overlay';
import { generateQuestionTuning } from './question-tuning';

// Core bootstrap
import { generatePreambleBash } from './preamble/generate-preamble-bash';
import { generateUpgradeCheck } from './preamble/generate-upgrade-check';
import { generateCompletionStatus, generatePlanModeInfo } from './preamble/generate-completion-status';

// One-time onboarding prompts
import { generateLakeIntro } from './preamble/generate-lake-intro';
import { generateTelemetryPrompt } from './preamble/generate-telemetry-prompt';
import { generateProactivePrompt } from './preamble/generate-proactive-prompt';
import { generateFirstRunGuidance } from './preamble/generate-first-run-guidance';
import { generateRoutingInjection } from './preamble/generate-routing-injection';
import { generateVendoringDeprecation } from './preamble/generate-vendoring-deprecation';
import { generateSpawnedSessionCheck } from './preamble/generate-spawned-session-check';
import { generateWritingStyleMigration } from './preamble/generate-writing-style-migration';

// Host-specific instructions
import { generateBrainHealthInstruction } from './preamble/generate-brain-health-instruction';

// GBrain cross-machine sync
import { generateBrainSyncBlock } from './preamble/generate-brain-sync-block';

// Behavioral / voice
import { generateVoiceDirective } from './preamble/generate-voice-directive';

// Tier 2+ context and interaction framework
import { generateContextRecovery } from './preamble/generate-context-recovery';
import { generateAskUserFormat } from './preamble/generate-ask-user-format';
import { generateWritingStyle } from './preamble/generate-writing-style';
import { generateCompletenessSection } from './preamble/generate-completeness-section';
import { generateConfusionProtocol } from './preamble/generate-confusion-protocol';
import { generateEvidenceDirective } from './preamble/generate-evidence-directive';
import { generateContinuousCheckpoint } from './preamble/generate-continuous-checkpoint';
import { generateContextHealth } from './preamble/generate-context-health';

// PREOS cross-cutting project-contract handoff for canonical stages.
import { generatePreosContext } from './preamble/generate-preos-context';

// Tier 3+ repo mode + search
import { generateRepoModeSection } from './preamble/generate-repo-mode-section';
import { generateSearchBeforeBuildingSection } from './preamble/generate-search-before-building';
import { generateMakePdfSetup } from './make-pdf';

export { generateTestFailureTriage } from './preamble/generate-test-failure-triage';

// Preamble Composition (tier → sections)
// T1: core + upgrade + lake + telemetry + PREOS handoff where applicable + voice(trimmed) + completion
// T2: T1 + voice(full) + ask + completeness + context-recovery + confusion + checkpoint + context-health
// T3: T2 + repo-mode + search
// T4: same as T3; TEST_FAILURE_TRIAGE is a separate placeholder.
export function generatePreamble(ctx: TemplateContext): string {
  const tier = ctx.preambleTier;
  if (tier === undefined) {
    throw new Error(
      `Missing preamble-tier frontmatter in ${ctx.tmplPath}: every template that ` +
      `resolves {{PREAMBLE}} must declare 'preamble-tier: N' (1-4).`
    );
  }
  if (tier < 1 || tier > 4) {
    throw new Error(`Invalid preamble-tier: ${tier} in ${ctx.tmplPath}. Must be 1-4.`);
  }
  const sections = [
    generatePreambleBash(ctx),
    ...(ctx.skillName === 'make-pdf' ? [generateMakePdfSetup(ctx)] : []),
    generatePlanModeInfo(ctx),
    generateUpgradeCheck(ctx),
    generateWritingStyleMigration(ctx),
    generateLakeIntro(ctx),
    generateTelemetryPrompt(ctx),
    generateProactivePrompt(ctx),
    generateFirstRunGuidance(ctx),
    generateRoutingInjection(ctx),
    generateVendoringDeprecation(ctx),
    generateSpawnedSessionCheck(),
    generateBrainHealthInstruction(ctx),
    ...(tier >= 2 ? [generateAskUserFormat(ctx)] : []),
    generateBrainSyncBlock(ctx),
    generateModelOverlay(ctx),
    generatePreosContext(ctx),
    generateVoiceDirective(tier),
    ...(tier >= 2 ? [
      generateContextRecovery(ctx),
      generateWritingStyle(ctx),
      generateCompletenessSection(ctx),
      generateConfusionProtocol(ctx),
      generateEvidenceDirective(ctx),
      generateContinuousCheckpoint(),
      generateContextHealth(ctx),
      generateQuestionTuning(ctx),
    ] : []),
    ...(tier >= 3 ? [generateRepoModeSection(), generateSearchBeforeBuildingSection(ctx)] : []),
    generateCompletionStatus(ctx),
  ];
  return sections.filter(s => s && s.trim().length > 0).join('\n\n');
}
