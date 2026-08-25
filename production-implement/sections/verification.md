<!-- AUTO-GENERATED from verification.md.tmpl — do not edit directly -->
<!-- Regenerate: bun run gen:skill-docs -->
## Verification, self-attack and evidence

Verification is incremental and accompanies implementation. Applicable tests include unit, integration, contract, end-to-end, concurrency, duplicate submission, retry, timeout, out-of-order event, stale-data, permission, cross-tenant, abuse/security, load/stress/soak, failure injection, provider/cache/queue/database outage, restore, migration, rollback, cost, reconciliation and invariant tests.

For every material change perform a self-attack pass focused on:

- unauthorized access/tenant leakage;
- silent data corruption/wrong business result;
- duplicate or partial side effects;
- concurrency/race/locking behavior;
- dependency timeout/retry storms;
- failure/degradation/recovery;
- performance/resource exhaustion;
- economic abuse and cost explosion;
- migration/rollback incompatibility;
- human/operator mistakes.

Use existing `gstack-evidence run --label <label> -- <command...>` for command/test execution evidence wherever possible. PREOS evidence records reference that ledger/log and additionally bind risk/control IDs, environment, configuration version, approval links, freshness and invalidation rules.

Gate values are `GREEN`, `AMBER`, `RED`, `HUMAN REVIEW`, `UNKNOWN`. UNKNOWN never becomes GREEN by omission. A downstream control cannot GREEN while a prerequisite control is RED/UNKNOWN/HUMAN REVIEW.

A critical RED blocks unless an authorized, scoped, non-expired human risk acceptance exists with reason, compensating controls and review trigger.
