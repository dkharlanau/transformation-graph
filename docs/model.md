# Canonical model v0.1

Transformation Graph is deliberately small. The canonical file contains four top-level elements: `version`, `project`, `nodes`, and `edges`.

## Canonical node types

| Type | Meaning |
| --- | --- |
| `process` | End-to-end business or transformation process |
| `process_step` | A step inside a process |
| `system` | Source, target, middleware, SaaS, data platform, or other system |
| `business_object` | Business-level object such as Customer, Material, Sales Order |
| `data_object` | Table, file, message, API payload, CDS view, dataset |
| `field` | Field or attribute that needs field-level lineage |
| `interface` | Integration or migration interface |
| `mapping` | Mapping specification |
| `rule` | Business, transformation, validation, or derivation rule |
| `requirement` | Functional/non-functional requirement |
| `test` | Test, control, or reconciliation |
| `change` | Change item, scope item, defect, migration impact |
| `owner` | Team, role, or accountable party |
| `decision` | Architecture or project decision |
| `evidence` | Document, ticket, workbook, log, sign-off, or other evidence |

Projects can add experimental node types using the `x-` prefix, for example `x-cutover-task`.

## Edges

Edges are intentionally open-vocabulary in v0.1. A relation is a lowercase identifier such as `contains`, `runs_on`, `reads`, `writes`, `uses`, `maps_to`, `sends_to`, `covered_by`, `validates`, `affects`, `depends_on`, `owned_by`, `governed_by`, or `evidenced_by`.

## Deterministic invariants

The CLI currently enforces:

1. Model version is `0.1`.
2. `project.id` and `project.name` exist.
3. Node IDs are unique.
4. Node types are canonical or use the `x-` extension prefix.
5. Every edge endpoint resolves to an existing node.
6. Exact duplicate edges are rejected.
7. Tags are string lists and attributes are objects.

The JSON Schema defines the structural contract. The Python validator adds cross-reference checks that JSON Schema alone cannot express cleanly.

## ID convention

Prefer stable IDs that survive title changes, for example `system.s4`, `object.customer`, `mapping.customer-to-bp`, and `test.customer-load`. Do not encode volatile status, dates, or display labels into IDs.

## Why one graph?

The graph is not intended to replace Jira, SAP Cloud ALM, Signavio, LeanIX, Excel mappings, or architecture tools. It creates a project-scoped connective layer so a transformation team can answer questions across them: what breaks if a field changes, which tests cover a mapping, which decision introduced a rule, which interfaces touch an object, and which changes have no test or owner.
