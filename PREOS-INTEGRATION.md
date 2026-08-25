# PREOS Integration Contract

This repository participates in the integrated AI Product Delivery Blueprint + PREOS + gstack + Codex software production system.

PREOS means Production Risk, Economics, and Evolution Operating System. Its canonical implementation lives in `WilsonMisor/PREOS`. The governing AI Product Delivery Blueprint lives in `WilsonMisor/wed_dev_skill`.

## Responsibility boundary

Within the integrated system:

1. The AI Product Delivery Blueprint governs lifecycle, approved baselines, active profiles, task packets, gate requirements, and change control.
2. PREOS determines required production-assurance analysis/evidence: risks, controls, economics, evidence freshness, failure/recovery/reconciliation needs, release assurance, and production learning.
3. gstack supplies specialist engineering review, investigation, QA, benchmarking, shipping, deployment execution, canary verification, documentation, and retrospective capabilities.
4. Codex implements approved bounded AI Task Packets.
5. Accountable humans accept consequential risk and authorize production.
6. The application repository remains the execution surface for product code and project-specific artifacts.

These are integrated responsibility layers, not one combined repository. Do not vendor PREOS or the Blueprint into gstack merely to make them cooperate.

## PREOS-to-gstack routing

When PREOS or the Blueprint identifies a specialist need, use the namespaced Codex installation where available:

| Assurance need | gstack specialist |
| --- | --- |
| Problem reframing / assumptions | `gstack-office-hours` |
| Product value / scope challenge | `gstack-plan-ceo-review` |
| Architecture, failure modes, data/state review | `gstack-plan-eng-review` |
| Planned UX/UI quality | `gstack-plan-design-review` |
| Design-system direction | `gstack-design-consultation` |
| Alternative design exploration | `gstack-design-shotgun` |
| Approved design to HTML where architecture permits | `gstack-design-html` |
| Developer-product experience | `gstack-plan-devex-review` / `gstack-devex-review` |
| Security / threat review | `gstack-cso` |
| Code / implementation review | `gstack-review` |
| Root-cause investigation | `gstack-investigate` |
| Browser/workflow QA with authorised remediation | `gstack-qa` |
| Non-mutating browser/workflow QA | `gstack-qa-only` |
| Implemented UI design audit | `gstack-design-review` |
| Browser research / inspection | `gstack-browse` |
| Performance / comparative evidence | `gstack-benchmark` |
| Release preparation | `gstack-ship` |
| Approved production landing/deployment | `gstack-land-and-deploy` |
| Canary verification | `gstack-canary` |
| Release documentation | `gstack-document-release` |
| Governed documentation | `gstack-document-generate` |
| Post-release reflection | `gstack-retro` |

Optional execution-safety tools such as `gstack-careful`, `gstack-freeze`, `gstack-guard`, and `gstack-unfreeze` may add safety but never replace Blueprint/PREOS gates, repository permissions, or accountable human approval.

## Handoff contract from PREOS / Blueprint

A specialist request should provide only the relevant bounded context, including as applicable:

1. Project Classification Record and PREOS assurance level/maturity stage.
2. Active Blueprint profiles.
3. PREOS Project Contract identifier/version/hash.
4. Relevant requirement IDs.
5. Relevant risk IDs and control IDs.
6. Applicable G0-G11 gate/evidence question.
7. Applicable ADRs, canonical domain/API/data contracts, and design baseline.
8. Threat/security/privacy/control context when relevant.
9. Current AI Task Packet or review scope.
10. Known risks, accepted exceptions, and role/authority constraints.
11. Required evidence format and freshness binding.
12. Explicit mutation permission: review-only or authorised remediation.

Do not ask a gstack specialist to infer the entire product when approved governing artifacts exist.

## Output contract back to PREOS / Blueprint

The specialist should return, as applicable:

1. findings tied to supplied requirement/risk/control IDs;
2. severity and evidence;
3. tests or reproduction steps;
4. changed files when mutation was explicitly authorised;
5. unresolved uncertainty;
6. recommendation or remediation evidence;
7. whether supplied acceptance criteria were met.

A gstack result is specialist evidence, not an automatic PREOS GREEN result or Blueprint gate approval.

## Authority rule

gstack must not:

1. silently change an approved PRD/SRS/SRD/architecture/design baseline;
2. broaden an AI Task Packet into adjacent work without approval;
3. convert PREOS UNKNOWN/HUMAN REVIEW/RED into GREEN;
4. accept security, privacy, financial, legal, operational, or production risk on behalf of a human;
5. authorize production merely because `gstack-ship` or `gstack-land-and-deploy` is available;
6. store authoritative PREOS state under gstack state directories.

If gstack advice conflicts with a hard Blueprint/PREOS rule or approved project baseline, record the conflict and route it to accountable human resolution.

## State separation

PREOS project state belongs under `.ai-product-delivery/preos/` in the application repository and PREOS runtime/recovery state belongs under `PREOS_STATE_ROOT`.

gstack owns only its own runtime/tool state. `GSTACK_STATE_ROOT` must not become the PREOS source of truth.

## Release relationship

The normal release relationship is:

```text
Blueprint launch readiness
        |
PREOS G0-G11 assurance
        |
accountable human production approval
        |
gstack-ship
        |
gstack-land-and-deploy (when selected)
        |
gstack-canary / verification
        |
production telemetry and incidents
        |
PREOS production learning
        |
gstack-retro
        |
Blueprint change control
```

Execution commands occur after the required authority gate; they are not the authority gate.