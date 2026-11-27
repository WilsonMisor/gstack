# gstack Progressive-Disclosure Refactor Plan

## Problem

Large skill files undermine the same progressive-disclosure strategy used by Codex skills. The generated `autoplan/SKILL.md` must not remain the place where every reusable preamble, persona, review method, audit rule and final gate is embedded.

## Required architecture

Keep `autoplan/SKILL.md.tmpl` as a small router, ideally below 300 lines and subject to CI warning above 500 lines. Move detailed sections into `autoplan/references/` and load only the references needed by the active autoplan phase. Generated `SKILL.md` remains generated and must never be hand-edited.

Suggested references:

- `references/preamble.md`
- `references/question-protocol.md`
- `references/ceo-review.md`
- `references/design-review.md`
- `references/engineering-review.md`
- `references/dx-review.md`
- `references/final-gate.md`
- `references/audit-trail.md`

## Repository-wide enforcement

1. Add a script that measures every generated and template skill by lines, bytes and approximate tokens.
2. Fail CI when a router crosses the hard review threshold without an approved exception.
3. Detect duplicated preambles across skills.
4. Require large knowledge material to live in `references/`.
5. Preserve current generated-file rules: edit `.tmpl`, regenerate outputs, then test.
6. Add regression tests proving that the router still exposes all phases after splitting.
7. Do not load PREOS catalogues into gstack. gstack requests bounded assurance results through the integration contract.
