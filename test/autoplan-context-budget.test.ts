import { describe, test, expect } from 'bun:test';
import * as fs from 'fs';
import * as path from 'path';

const ROOT = path.resolve(import.meta.dir, '..');

function read(rel: string): string {
  return fs.readFileSync(path.join(ROOT, rel), 'utf-8');
}

describe('autoplan progressive-disclosure carve', () => {
  test('source template is a section router and keeps PREOS handoff in the skeleton', () => {
    const tmpl = read('autoplan/SKILL.md.tmpl');
    expect(tmpl).toContain('{{SECTION_INDEX:autoplan}}');
    expect(tmpl).toContain('{{SECTION:review-phases}}');
    expect(tmpl).toContain('## Important Rules');
    expect(tmpl).toContain('## Governed implementation handoff');
    expect(tmpl).toContain('gstack-preos-handoff');
    expect(tmpl).not.toContain('## Phase 1: CEO Review (Strategy & Scope)');
    expect(tmpl).not.toContain('## Phase 4: Final Approval Gate');
    expect(tmpl.split('\n').length).toBeLessThanOrEqual(300);
  });

  test('review-phases section preserves the detailed autoplan workflow', () => {
    const section = read('autoplan/sections/review-phases.md.tmpl');
    for (const marker of [
      '## The 6 Decision Principles',
      '## Decision Classification',
      '## Phase 0: Intake + Restore Point',
      '## Phase 1: CEO Review (Strategy & Scope)',
      '## Phase 2: Design Review',
      '## Phase 3: Eng Review + Dual Voices',
      '## Phase 3.5: DX Review',
      '## Phase 4: Final Approval Gate',
      '## Completion: Write Review Logs',
    ]) {
      expect(section).toContain(marker);
    }
  });

  test('generated skeleton routes to the generated section and the union keeps phase anchors', () => {
    const skeleton = read('autoplan/SKILL.md');
    const section = read('autoplan/sections/review-phases.md');
    const union = `${skeleton}\n${section}`;
    expect(skeleton).toContain('## Section index');
    expect(skeleton).toContain('sections/review-phases.md');
    expect(skeleton).not.toContain('## Phase 4: Final Approval Gate');
    expect(union).toContain('## Phase 4: Final Approval Gate');
    expect(union).toContain('## Governed implementation handoff');
    expect(union).toContain('accountable human production approval');
  });
});

describe('cross-repo ownership reference', () => {
  test('keeps gstack as specialist authority only', () => {
    const ownership = JSON.parse(read('integration/repository-ownership.json'));
    const gstack = ownership.repositories['WilsonMisor/gstack'];
    expect(gstack.authority).toContain('specialist engineering review');
    expect(ownership.prohibitions).toContain('Do not allow gstack shipping or successful tests to self-authorize production.');
  });
});
