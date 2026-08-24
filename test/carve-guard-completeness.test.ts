/**
 * E1 — legacy carve-guard completeness meta-guard (GATE tier, free).
 *
 * Makes the historical carve gap impossible to reopen: every legacy skill
 * carved on disk (owns a sections/manifest.json and is not a native-sectioned
 * PREOS skill) MUST be in the canonical CARVE_GUARDS registry, and vice-versa.
 * PREOS Stage 0/5 were born sectioned rather than carved from the historical
 * v1.64.1.0 baseline; their manifests/routing are guarded separately by
 * test/production-engine/codex-generation.test.ts.
 *
 * Because the static (E2) and behavioral (T2) legacy-carve guards are
 * data-driven FROM CARVE_GUARDS, registry membership remains guard coverage for
 * every historical carve.
 */

import { describe, test, expect } from 'bun:test';
import * as path from 'path';
import { checkCompleteness } from './helpers/carve-guard-checks';

const ROOT = path.resolve(import.meta.dir, '..');

describe('carve-guard completeness (gate, free)', () => {
  test('filesystem legacy-carved set == CARVE_GUARDS set, and every entry is consistent', () => {
    expect(checkCompleteness(ROOT)).toEqual([]);
  });
});
