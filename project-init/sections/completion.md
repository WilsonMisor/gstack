<!-- AUTO-GENERATED from completion.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->
## Stage 0 completion and approval

Before completion verify:

- safe source manifest exists and has hashes;
- authority classification exists for every material source;
- no unresolved material source conflict remains;
- requirements retain source traceability;
- architecture/stack/context are explicit rather than guessed;
- roles, role gaps and human decision authorities are explicit;
- assumptions are visible;
- current external research flags are visible;
- Project Contract status is not STALE;
- original inputs remain unchanged.

Present the contract summary and material assumptions/conflicts to the human.
The model cannot approve its own Project Contract. Record explicit approval in `approval-log.jsonl` with authority, timestamp, scope and contract version, then set contract status `APPROVED`.

Output exactly one terminal status:

- `PROJECT CONTRACT APPROVED — Stage 0 complete; proceed to $office-hours.`
- `BLOCKED — <reason>`

Never write application code in this skill.
