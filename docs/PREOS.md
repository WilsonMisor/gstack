# PREOS in gstack

PREOS (Production Risk, Economics, and Evolution Operating System) extends gstack with a deterministic Stage 0 `$project-init` and Stage 5 `$production-implement` while preserving the existing user-facing pipeline:

0. `$project-init`
1. `$office-hours`
2. `$plan-ceo-review`
3. `$plan-eng-review`
4. `$autoplan`
5. `$production-implement`
6. `$review`
7. `$qa`
8. `$ship`
9. `$land-and-deploy`
10. `$canary`

The eight PREOS engines — Context, Risk Generation, Change Impact, Economics & Complexity, Evolution, Control & Evidence, Production Feedback & Learning, Human Authority & Governance — are cross-cutting intelligence inside these stages, not additional mandatory user-facing stages.

The original 75 controls are the immutable deterministic minimum. Applicability is `Applies`, `Conditional`, `Not applicable`, `Escalate`, `Forbidden`. Evidence/gates are `GREEN`, `AMBER`, `RED`, `HUMAN REVIEW`, `UNKNOWN`; UNKNOWN never silently becomes GREEN. The seven original production gates remain Architecture, Security, Data, Performance, Failure, Deployment, Operations.

Stage 5 can emit `IMPLEMENTATION COMPLETE` or `BLOCKED`, never `PRODUCTION APPROVED`. Human approvals are explicit, persistent, scoped and never inferred after recovery. Existing specialist domain skills stay independent and bind through the Project Contract rather than being absorbed into gstack.

PREOS is anti-overengineering: completeness applies inside the human-approved lake; adjacent expansion, new infrastructure/vendors, material security/privacy/data/financial boundaries and irreversible actions require the appropriate authority. Deferred complexity requires a simpler current solution, measurable activation trigger and migration path.
