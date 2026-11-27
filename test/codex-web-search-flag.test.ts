/**
 * Deprecated codex web-search flag tripwire (#2525).
 *
 * codex >=0.144 deprecates `--enable web_search_cached` (its `--enable
 * <FEATURE>` surface now means `-c features.<name>=true`); the replacement
 * is `-c 'web_search="cached"'`, owned by ONE constant:
 * CODEX_WEB_SEARCH_FLAG in scripts/resolvers/constants.ts. Resolvers
 * interpolate it; templates reference {{CODEX_WEB_SEARCH_FLAG}}.
 *
 * These tests fail CI if the deprecated spelling re-enters any source
 * (resolver, template, helper) or any rendered SKILL.md / section / golden.
 */
import { describe, test, expect } from 'bun:test';
import * as fs from 'fs';
import * as path from 'path';
import { CODEX_WEB_SEARCH_FLAG } from '../scripts/resolvers/constants';

const ROOT = path.join(import.meta.dir, '..');
const DEPRECATED = '--enable web_search_cached';

function grepRepo(pattern: string, includes: string[]): string[] {
  // Traverse only repository text, without POSIX shell quoting or following
  // installation symlinks. Prune dependencies before scanning their contents.
  const hits: string[] = [];
  function walk(directory: string) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) continue;
      if (entry.isDirectory()) {
        if (!['node_modules', '.git', '.claude'].includes(entry.name)) walk(file);
      } else if (entry.isFile() && includes.some((glob) =>
        glob.startsWith('*.') ? entry.name.endsWith(glob.slice(1)) : entry.name === glob)) {
        if (file === path.join(ROOT, 'test/codex-web-search-flag.test.ts')) continue;
        if (fs.readFileSync(file, 'utf-8').includes(pattern)) hits.push(file);
      }
    }
  }
  walk(ROOT);
  return hits;
}

describe('deprecated codex web-search flag is gone (#2525)', () => {
  test('the replacement flag has exactly the documented shape', () => {
    expect(CODEX_WEB_SEARCH_FLAG).toBe(`-c 'web_search="cached"'`);
  });

  test('no rendered SKILL.md or section carries the deprecated flag', () => {
    const hits = grepRepo(DEPRECATED, ['SKILL.md', '*.md']);
    expect(hits).toEqual([]);
  });

  test('no source file (resolver, template, helper) carries the deprecated flag', () => {
    const hits = grepRepo(DEPRECATED, ['*.ts', '*.tmpl']);
    expect(hits).toEqual([]);
  });

  test('rendered codex skill actually resolves the token to the live flag', () => {
    const rendered = fs.readFileSync(path.join(ROOT, 'codex', 'SKILL.md'), 'utf-8');
    expect(rendered).toContain(CODEX_WEB_SEARCH_FLAG);
    expect(rendered).not.toContain('{{CODEX_WEB_SEARCH_FLAG}}');
  });

  test('rendered autoplan skill resolves the token at every inline site', () => {
    const main = fs.readFileSync(path.join(ROOT, 'autoplan', 'SKILL.md'), 'utf-8');
    expect(main).toContain('sections/review-phases.md');
    const rendered = main + fs.readFileSync(path.join(ROOT, 'autoplan', 'sections', 'review-phases.md'), 'utf-8');
    const count = rendered.split(CODEX_WEB_SEARCH_FLAG).length - 1;
    expect(count).toBeGreaterThanOrEqual(4);
    expect(rendered).not.toContain('{{CODEX_WEB_SEARCH_FLAG}}');
  });
});
