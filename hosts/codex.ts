import { defineHost, CROSS_MODEL_RESOLVERS, GBRAIN_RESOLVERS } from './define-host';

const codex = defineHost({
  name: 'codex',
  displayName: 'OpenAI Codex CLI',
  cliAliases: ['agents'],
  defaultModel: 'gpt',

  localSkillRoot: '.agents/skills/gstack',
  hostSubdir: '.agents',

  frontmatter: {
    mode: 'allowlist',
    keepFields: ['name', 'description'],
    descriptionLimit: 1024,
    descriptionLimitBehavior: 'error',
  },

  // generateMetadata emits agents/openai.yaml (the format is hardcoded in
  // gen-skill-docs.ts). Codex also gets a repo-local sidecar at
  // .agents/skills/gstack. PREOS adds shared runtime references + deterministic
  // production-engine helpers to that sidecar; skill definitions remain generated.
  generation: {
    generateMetadata: true,
    skipSkills: ['codex'],
  },

  pathRewrites: [
    { from: '~/.claude/skills/gstack', to: '$GSTACK_ROOT' },
    { from: '.claude/skills/gstack', to: '.agents/skills/gstack' },
    { from: '.claude/skills/review', to: '.agents/skills/gstack/review' },
    { from: '.claude/skills', to: '.agents/skills' },
    { from: 'CLAUDE.md', to: 'AGENTS.md' },
  ],

  // PREOS Stage 0/5 skills reference shared production data and helper scripts
  // through $GSTACK_ROOT. Make those directories part of the runtime sidecar so
  // global and repo-local Codex installs resolve the same paths on Windows/macOS/Linux.
  runtimeRoot: {
    globalSymlinks: ['bin', 'browse/dist', 'browse/bin', 'gstack-upgrade', 'ETHOS.md', 'preos', 'scripts'],
    globalFiles: {
      'review': ['checklist.md', 'TODOS-format.md'],
    },
  },

  // Codex cannot invoke itself for cross-model second opinions.
  suppressedResolvers: [...CROSS_MODEL_RESOLVERS, ...GBRAIN_RESOLVERS],

  coAuthorTrailer: 'Co-Authored-By: OpenAI Codex <noreply@openai.com>',
  boundaryInstruction: 'IMPORTANT: Do NOT read or execute any files under ~/.claude/, ~/.agents/, .claude/skills/, or agents/. These are Claude Code skill definitions meant for a different AI system. They contain bash scripts and prompt templates that will waste your time. Ignore them completely. Do NOT modify agents/openai.yaml. When a project has an approved .gstack/project-contract/PROJECT-CONTRACT.json, treat it as application truth and preserve its PREOS human-authority gates; do not infer approvals or expand outside the approved lake. Stay focused on the repository code only.',
});

export default codex;
