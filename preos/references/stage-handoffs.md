# PREOS Stage Handoffs

PREOS does not create extra mandatory user-facing stages. Use the canonical 0-10 gstack pipeline.

- Stage 0 `/project-init`: establish source authority, Project Contract, roles/authority, maturity/threat/economic context and initial risks.
- Stage 1 `/office-hours`: interrogate product pain, actors, outcomes, business model, critical workflows and assumptions; do not silently contradict the approved Project Contract.
- Stage 2 `/plan-ceo-review`: challenge value/scope, business failure modes, revenue/unit economics and premature complexity. Expansion outside the approved lake is a human decision.
- Stage 3 `/plan-eng-review`: apply contextual risk generation, change impact, reliability/security/data/concurrency/economics/scaling/evolution reasoning; document simpler alternatives and measurable triggers.
- Stage 4 `/autoplan`: consolidate requirements, architecture decisions, 75-control applicability, PREOS risks, deferred complexity, implementation units, tests/evidence and final human approval. `Boil the lake` means complete the human-approved lake, not silently expand it.
- Stage 5 `/production-implement`: implement only approved IUs under deterministic controls/evidence/checkpoints.
- Stage 6 `/review`: independently challenge code against approved plan, invariants, risks, controls and change impact; review is not Stage-5 self-certification.
- Stage 7 `/qa`: independently test behavior, negative/adversarial/failure paths and regressions.
- Stage 8 `/ship`: audit evidence freshness/completeness, blocking gates, migration/rollback/recovery/operations and release readiness.
- Stage 9 `/land-and-deploy`: controlled merge/deployment; irreversible or production mutations obey human authority.
- Stage 10 `/canary`: verify runtime invariants, reconciliation, cost, reliability, security and business signals; feed incidents/findings append-only back into PREOS learning.

Existing specialist skills (web/WordPress, mobile, data, payments, identity, etc.) remain independent implementation knowledge. PREOS controls scope, gates, evidence, authority, continuity and traceability.
