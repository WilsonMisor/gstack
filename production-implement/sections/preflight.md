<!-- AUTO-GENERATED from preflight.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->
## Preflight — hard stop before code

1. Locate `<project-root>/.gstack/project-contract/PROJECT-CONTRACT.json`.
2. Run `bun "$GSTACK_ROOT/scripts/production-engine/validate-project-contract.ts" <contract> <project-root>`.
3. If missing, stale, conflicted or unapproved: **BLOCK** and route to `$project-init`.
4. Locate the approved Stage-4 plan. It must identify its approval, scope/lake, contract version and intended implementation target. Missing approval blocks Stage 5.
5. Run `bun "$GSTACK_ROOT/scripts/production-engine/state-reconcile.ts"` before creating a new state. If it returns `RECOVERY_CONFLICT`, stop. If human approval is pending, keep it pending. Never infer approval after a restart.
6. Confirm current branch is a development branch, not a protected production/main branch unless the Project Contract explicitly authorizes that workflow.
7. Revalidate the narrow scope, actual stack, selected overlay, user types, data touched, external dependencies, scale/failure impact and material changes since the plan.
8. If project source/plan/code disagree materially, record conflict and BLOCK. Do not pick a side silently.

No code edit, migration, package install, external service creation or production mutation may occur before this section passes.
