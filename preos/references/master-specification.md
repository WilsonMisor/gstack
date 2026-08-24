# PREOS Master Runtime Specification

PREOS is the Production Risk, Economics, and Evolution Operating System used by gstack. It is software-neutral and applies to SaaS, web, mobile, marketplaces, FinTech, HealthTech, enterprise, consumer, e-commerce, logistics, education, government, AI/data systems, collaboration, media, subscriptions and internal tools.

## Eight engines
1. Context Engine — product, actors, business/revenue model, money, sensitive/regulated data, workflows, providers, jurisdictions, scale, availability/recovery, budget, maturity, trust, roles and authorities.
2. Risk Generation Engine — generate contextual failures from Feature × actor × input × state × time × concurrency × retry × network × dependency × storage × permission × attack × scale × cost × human action × business rule × legal consequence × recovery. Materialize high-value combinations, not an uncontrolled Cartesian product.
3. Change Impact Engine — affected components/users/data/interfaces/migrations/security and financial boundaries, blast radius, deployment ordering, old/new coexistence, rollback and irreversibility.
4. Economics & Complexity Engine — fixed/variable/unit costs, support/AI/vendor/logging/egress/recovery/toil costs, cost concentration, economic abuse, complexity tax and cost of failure.
5. Evolution Engine — Required now / Required soon / Design now implement later / Optional / Not applicable / Premature complexity / Deferred with measurable activation trigger and migration path.
6. Control & Evidence Engine — immutable 75-control baseline + contextual risks; tests, evidence freshness, dependencies, reconciliation, invariants and GREEN/AMBER/RED/HUMAN REVIEW/UNKNOWN gates.
7. Production Feedback & Learning Engine — incidents add atomic risks, regression tests, monitoring/runbooks, architecture/economic/security review triggers; history is append-only.
8. Human Authority & Governance Engine — explicit owners, implementers, reviewers/approvers, escalation owners, role gaps and non-inferable human approvals/risk acceptance.

## Production reality assumptions
Users make mistakes, double-submit and abandon operations. Networks fail/retry/reorder. Servers/processes/databases/replicas/queues/caches/providers fail or return stale/bad results. Attackers automate abuse. Fraud evolves. Employees/admins err or abuse privileges. Secrets leak. Traffic/data/support/cost grow unevenly. A system can be available while silently wrong or economically unviable. Backups are meaningless until restore is proven. Deployments can succeed while breaking old clients.

## Mandatory models
Product maturity: Stage 0 Prototype; 1 Early Production; 2 Product Traction; 3 Scaling Product; 4 Large Platform; 5 High Assurance/Global Platform.
Threat growth: Stage 0 low visibility; 1 generic scanners/spam/credential attacks/scraping; 2 economically motivated abuse/fraud; 3 targeted account takeover/DDoS/API/insider/organized fraud; 4 strategic/supply-chain/extortion/highly targeted attacks.

## Anti-overengineering
For every technology/control ask what concrete problem exists now, cheaper alternative, simple vs complex cost, operational burden, specialist knowledge, new failure modes, measurable adoption trigger and migration path. Never recommend Redis/Kafka/Kubernetes/search clusters/read replicas/microservices/service mesh/sharding/multi-region/data lake/graph/CQRS/event sourcing or similar merely because hyperscale systems use them.

## Cross-cutting domains
At minimum reason across product/business rules; data semantics; databases; frontend; mobile; APIs; authentication; authorization/tenant isolation; trust/verification/reputation; trade assurance; financial correctness; billing/subscriptions; files/storage; queues/events/background work; caching; search; notifications; networking; cloud/compute; scale/capacity; adaptive complexity; FinOps; security; privacy/data lifecycle; CI/CD/version control; observability; reliability; backup/DR; human/insider risk; support/operations; legal/contract/evidence; AI-specific risk; configuration/feature state; supply chain/build provenance; feature lifecycle/product debt; change impact; compatibility/version evolution; temporal correctness; data lineage; data quality; automated decisions; economic abuse; organizational knowledge/bus factor; vendor viability; critical account/domain ownership; multidimensional capacity; evidence freshness; control dependencies; risk aggregation; risk acceptance lifecycle; human authority; AI coding-agent authority.

## Nondeferrable first-production fundamentals
Correct data semantics and money representation; authentication where identity exists; authorization/tenant isolation; TLS; secrets management; database integrity; backups plus restore capability; input validation; idempotency for dangerous operations; audit for high-risk actions; error monitoring; basic rate/abuse limits; safe deployment; dependency timeouts; reconciliation where money/state must agree; obvious injection defenses; production environment separation. Expand based on context.

## Failure policy
For every dependency choose and justify one or more: fail open, fail closed, graceful degradation, queue for later, bounded retry, fallback provider, manual review, temporary suspension, full outage.

## Reconciliation and invariants
Reconcile systems that must agree: provider↔ledger, ledger↔bank, DB↔search/object storage, subscription↔billing/entitlements, event↔business result, analytics↔operations, verification provider↔status. Monitor context-specific invariants; examples: refund ≤ refundable amount, balanced ledger, payment requiring ledger entry has one, tenant record has valid tenant, verified claim has evidence.

## Evidence and completion
Evidence is bound to code/working tree, environment, configuration, time, producer and invalidation conditions. UNKNOWN is never GREEN. Aggregate scores cannot hide a critical RED. Risk acceptance is scoped, authorized, expiring and does not delete the risk. Stage 5 IMPLEMENTATION COMPLETE is not production approval.
