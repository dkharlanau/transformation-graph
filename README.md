# Transformation Graph

**A Git-native connective layer for enterprise transformations.**

Transformation Graph links processes, systems, business objects, data, fields, interfaces, mappings, rules, requirements, tests, changes, decisions, owners, and evidence in one project-scoped graph.

## What is executable today

- canonical YAML/JSON graph model and JSON Schema
- semantic validation with dangling-reference and duplicate detection
- realistic SAP S/4HANA customer migration example
- shortest dependency-path and bounded context queries
- impact traversal with direction/relation filters
- quality checks for orphan/coverage/evidence/ownership gaps
- Mermaid export for full or focused graph views
- generic CSV node/edge import
- deterministic composition of multiple graph slices
- pytest suite and GitHub Actions quality gate

No SAP system access is required.

## Quick start

```bash
git clone https://github.com/dkharlanau/transformation-graph.git
cd transformation-graph
python -m pip install -e ".[dev]"
transformation-graph validate examples/sap-s4-customer-migration.yaml
transformation-graph quality examples/sap-s4-customer-migration.yaml
transformation-graph impact examples/sap-s4-customer-migration.yaml change.bp-model --depth 2
```

Import an existing tabular inventory and compose slices:

```bash
transformation-graph import-csv --nodes nodes.csv --edges edges.csv --project-id demo --project-name "Demo" --output demo.yaml
transformation-graph compose process.yaml data.yaml interfaces.yaml --project-id program --project-name "Program Graph" --output program.yaml
```

Generate a focused Mermaid diagram:

```bash
transformation-graph mermaid examples/sap-s4-customer-migration.yaml --focus mapping.customer-to-bp --depth 1
```

## Why this exists

Enterprise transformation knowledge is usually fragmented across architecture slides, Excel mappings, Jira, process documents, test evidence, and people's heads. A field changes: which mapping uses it, which interface moves it, which test covers it, which decision created the rule, and which process is affected? Transformation Graph creates the missing cross-artifact dependency layer.

## Core model

```mermaid
graph LR
  P[Process] --> S[Process step]
  S --> SYS[System]
  S --> I[Interface]
  S --> M[Mapping]
  M --> D[Data / fields]
  M --> R[Rule]
  REQ[Requirement] --> T[Test]
  T --> I
  C[Change] --> D
  C --> DEC[Decision]
  DEC --> R
  DEC --> O[Owner]
  M --> E[Evidence]
```

See [docs/model.md](docs/model.md), [docs/queries.md](docs/queries.md), [docs/quality.md](docs/quality.md), and [docs/importing.md](docs/importing.md).

## Agent-ready by design

The useful AI pattern is not to send the whole project to a model. Resolve the node or change in question, traverse only relevant dependencies, emit a bounded context subgraph, let the model reason over explicit relationships, and keep deterministic validation outside the model.

## Related projects

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph)
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code)
- [Data Relationship Map](https://github.com/dkharlanau/data-relationship-map)
- [Cutover Graph](https://github.com/dkharlanau/cutover-graph)
- [Project Evidence Graph](https://github.com/dkharlanau/project-evidence-graph)

## Status

**MVP / v0.3.** The repository is executable and evolving through real transformation use cases.
