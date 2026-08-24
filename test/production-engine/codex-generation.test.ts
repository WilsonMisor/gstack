import { expect, test } from 'bun:test';
import { existsSync, readFileSync } from 'fs';
import { resolve } from 'path';

test('PREOS skills fit current gstack Codex host and discovery architecture', () => {
  const root=resolve(import.meta.dir,'../..');
  const host=readFileSync(resolve(root,'hosts/codex.ts'),'utf8');
  const discovery=readFileSync(resolve(root,'scripts/discover-skills.ts'),'utf8');
  expect(host).toContain("localSkillRoot: '.agents/skills/gstack'");
  expect(host).toContain("{ from: 'CLAUDE.md', to: 'AGENTS.md' }");
  expect(discovery).toContain('SKILL.md.tmpl');
  expect(existsSync(resolve(root,'project-init/SKILL.md.tmpl'))).toBe(true);
  expect(existsSync(resolve(root,'production-implement/SKILL.md.tmpl'))).toBe(true);
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
