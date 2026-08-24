# Evidence Policy

Verbal claims such as "security looks good", "backup configured", "scalable" or "payment safe" are not evidence. Applicable proof includes automated/integration/contract/concurrency/load/failure/security/restore/migration/rollback/reconciliation/invariant/cost tests; query plans; DB constraints; infrastructure config; runtime metrics/logs/traces; cost estimates/alerts; runbooks; audit events; architecture decisions; provider-failure tests; ownership and qualified human approval.

Evidence record fields include ID, produced_at, producer, source/log reference, environment, commit SHA or working-tree fingerprint, configuration version, related risks/controls/tests, validity/freshness, invalidation condition and revalidation trigger. Reuse `gstack-evidence` for command execution proof. Missing/stale evidence leaves the gate UNKNOWN/RED as policy requires; it never becomes GREEN by omission.
