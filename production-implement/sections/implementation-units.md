<!-- AUTO-GENERATED from implementation-units.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->
## Build Implementation Units

Break the approved lake into the smallest coherent **production-complete** Implementation Units, not the fewest lines of code.

Each IU must record:

- `iu_id`;
- requirement IDs;
- applicable 75-control numbers;
- PREOS risk IDs;
- files/components/data affected;
- dependencies and ordering;
- accountable/implementation/reviewer/approver/escalation roles;
- role gaps;
- change-impact analysis;
- tests and negative/failure tests;
- required evidence and freshness;
- monitoring/reconciliation where applicable;
- rollback/recovery plan;
- status: `READY`, `IMPLEMENTING`, `VERIFYING`, `VERIFIED`, `BLOCKED`, or `SUPERSEDED`.

For every IU explicitly ask what existing behavior must remain unchanged, what interfaces/data change, old/new version compatibility, deployment order, reversibility and what becomes irreversible.

### Human gates
Stop and request explicit human approval before material/new:

- architecture or technology-stack changes;
- paid/external dependencies or services;
- destructive/irreversible database, data, retention or privacy changes;
- authentication, authorization, tenant/RLS, secrets or security-boundary changes;
- production infrastructure/network/domain/queue/cache/CDN/storage changes;
- financial custody or regulated flows;
- scope expansion outside the approved lake;
- unresolved source/plan/code conflict;
- `Escalate` classifications or other high-impact uncertainty.

Completeness applies inside the approved lake. Adjacent work is reported, not silently implemented.
