<!-- AUTO-GENERATED from authority-resolution.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->
## Authority and conflict resolution

Classify every material source using this precedence:

1. explicit human-approved decision;
2. declared primary source of truth;
3. approved supporting specification;
4. existing code/infrastructure as observed state;
5. drafts, meeting notes, historical/superseded material as context only.

Write `source-authority.json` with authority level, rationale, supersession relationships, and affected requirement IDs.
Write every unresolved contradiction to `source-conflicts.json`.

**HARD GATE:** A material conflict between authoritative sources BLOCKS Stage 0. Do not silently choose the most convenient source and do not infer intent from code.

Assumptions must be explicit. Write them append-only to `assumption-register.jsonl` with status `OPEN`, source gap, impact, owner roles, and review trigger. High-impact assumptions require human resolution before approval.
