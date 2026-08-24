import { expect, test } from 'bun:test';
import { existsSync, readFileSync } from 'fs';
import { resolve } from 'path';

const NATIVE_SECTIONED: Record<string, string[]> = {
  'project-init': [
    'source-intake.md',
    'authority-resolution.md',
    'project-contract.md',
    'context-and-preos.md',
    'completion.md',
  ],
  'production-implement': [
    'preflight.md',
    'applicability.md',
    'implementation-units.md',
    'implementation.md',
    'verification.md',
    'continuity.md',
    'completion.md',
  ],
};

test('PREOS skills fit current gstack Codex host and discovery architecture', () => {
  const root=resolve(import.meta.dir,'../..');
  const host=readFileSync(resolve(root,'hosts/codex.ts'),'utf8');
  const discovery=readFileSync(resolve(root,'scripts/discover-skills.ts'),'utf8');
  expect(host).toContain("localSkillRoot: '.agents/skills/gstack'");
  expect(host).toContain("{ from: 'CLAUDE.md', to: 'AGENTS.md' }");
  expect(discovery).toContain('SKILL.md.tmpl');
  expect(discovery).toContain('sections');
  expect(existsSync(resolve(root,'project-init/SKILL.md.tmpl'))).toBe(true);
  expect(existsSync(resolve(root,'production-implement/SKILL.md.tmpl'))).toBe(true);
});

test('native-sectioned PREOS skills have complete manifests and generated section routing', () => {
  const root=resolve(import.meta.dir,'../..');
  for (const [skill, expectedFiles] of Object.entries(NATIVE_SECTIONED)) {
    const manifestPath=resolve(root,skill,'sections','manifest.json');
    expect(existsSync(manifestPath)).toBe(true);
    const manifest=JSON.parse(readFileSync(manifestPath,'utf8')) as {skill:string;sections:Array<{file:string}>};
    expect(manifest.skill).toBe(skill);
    expect(manifest.sections.map(s=>s.file)).toEqual(expectedFiles);
    for (const file of expectedFiles) {
      expect(existsSync(resolve(root,skill,'sections',`${file}.tmpl`))).toBe(true);
    }

    const generatedSkill=resolve(root,skill,'SKILL.md');
    if (!existsSync(generatedSkill)) continue;
    const skeleton=readFileSync(generatedSkill,'utf8');
    expect(skeleton).toContain('## Section index');
    expect(skeleton).toContain('> **STOP.**');
    for (const file of expectedFiles) {
      expect(skeleton).toContain(`sections/${file}`);
      const generatedSection=resolve(root,skill,'sections',file);
      expect(existsSync(generatedSection)).toBe(true);
      expect(readFileSync(generatedSection,'utf8').slice(0,220)).toContain('AUTO-GENERATED');
    }
  }
});

test('if Codex host artifacts were generated, both skills have SKILL.md and openai.yaml', () => {
  const root=resolve(import.meta.dir,'../..');
  for(const name of ['gstack-project-init','gstack-production-implement']) {
    const p=resolve(root,'.agents','skills',name,'SKILL.md');
    if(!existsSync(p)) continue;
    expect(readFileSync(p,'utf8')).toMatch(/^---\nname: (project-init|production-implement)\n/m);
    expect(existsSync(resolve(root,'.agents','skills',name,'agents','openai.yaml'))).toBe(true);
  }
});
