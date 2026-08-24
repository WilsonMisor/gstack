import { describe, expect, test } from 'bun:test';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = join(import.meta.dir, '..', '..');

function parseRows(markdown: string): Array<{ id: string; sourceRow: number }> {
  const rows: Array<{ id: string; sourceRow: number }> = [];
  for (const line of markdown.split(/\r?\n/)) {
    const match = line.match(/^\|\s*(WP-\d{3})\s*\|\s*(\d{1,2})\s*\|/);
    if (match) rows.push({ id: match[1], sourceRow: Number(match[2]) });
  }
  return rows;
}

describe('WordPress production overlay', () => {
  test('maps source rows 1..75 one-to-one to WP-001..WP-075', () => {
    const md = readFileSync(
      join(ROOT, 'production-implement', 'references', 'wordpress-classic-overlay.md'),
      'utf-8',
    );
    const rows = parseRows(md);
    expect(rows).toHaveLength(75);
    expect(rows.map((row) => row.id)).toEqual(
      Array.from({ length: 75 }, (_, i) => `WP-${String(i + 1).padStart(3, '0')}`),
    );
    expect(rows.map((row) => row.sourceRow)).toEqual(
      Array.from({ length: 75 }, (_, i) => i + 1),
    );
  });

  test('keeps the overlay subordinate to the immutable baseline and Project Contract', () => {
    const md = readFileSync(
      join(ROOT, 'production-implement', 'references', 'wordpress-classic-overlay.md'),
      'utf-8',
    );
    expect(md).toContain('does **not** replace the immutable FS-001..FS-075 baseline');
    expect(md).toContain('When the Project Contract selects this overlay');
    expect(md).toContain('no applicable gate, no passing test, no evidence, no acceptance');
  });
});
