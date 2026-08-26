# Transformation Graph

**A Git-native connective layer for enterprise transformations.**

Transformation Graph links processes, systems, business objects, data, fields, interfaces, mappings, rules, requirements, tests, changes, decisions, owners, and evidence in one project-scoped graph. It is designed for SAP and enterprise transformation work where useful knowledge otherwise lives across Excel, architecture diagrams, process documents, mapping workbooks, tickets, test evidence, and people's heads.

## What is executable today

- canonical YAML/JSON graph model and JSON Schema
- deterministic semantic validation, dependency paths, impact traversal, and quality checks
- realistic SAP S/4HANA customer migration example
- generic CSV and Excel ingestion
- Mapping as Code, Interface as Code, and Process as Code adapters
- deterministic graph composition across artifact slices
- configurable governance policy packs with CI failure thresholds
- semantic graph diff, neighboring change-impact, and Markdown/JSON PR review reports
- dependency-free HTML explorer with interactive SVG dependency canvas
- Mermaid export
- stable bounded agent context-pack contract with provenance
- optional MCP v2 server exposing graph resources and deterministic tools
- pytest suite and GitHub Actions quality/policy gates

No SAP system access is required.

## Quick start

```bash
git clone https://github.com/dkharlanau/transformation-graph.git
cd transformation-graph
python -m pip install -e ".[dev]"

transformation-graph validate examples/sap-s4-customer-migration.yaml
transformation-graph impact examples/sap-s4-customer-migration.yaml change.bp-model --depth 2
transformation-graph policy examples/sap-s4-customer-migration.yaml \
  --pack policies/enterprise-baseline.yaml --fail-on error
```

Generate a visual explorer:

```bash
transformation-graph html examples/sap-s4-customer-migration.yaml \
  --output transformation-graph.html
```

Generate a deterministic change-review report:

```bash
transformation-graph review \
  examples/change/before.yaml \
  examples/change/after.yaml \
  --impact-depth 2 \
  --policy policies/change-readiness.yaml \
  --output review.md
```

## Bring existing project artifacts into the graph

CSV inventories:

```bash
transformation-graph import-csv \
  --nodes nodes.csv --edges edges.csv \
  --project-id demo --project-name "Demo" \
  --output demo.yaml
```

Excel workbooks use the same contract in `Nodes` and `Edges` worksheets. Excel support is optional:

```bash
python -m pip install -e ".[excel]"
transformation-graph import-excel transformation-inventory.xlsx \
  --project-id program --project-name "S/4 Program" \
  --output program.yaml
```

Normalize neighboring as-code artifacts:

```bash
transformation-graph import-adapter mapping examples/adapters/mapping.yaml --output mapping.graph.yaml
transformation-graph import-adapter interface examples/adapters/interface.yaml --output interface.graph.yaml
transformation-graph import-adapter process examples/adapters/process.yaml --output process.graph.yaml

transformation-graph compose \
  mapping.graph.yaml interface.graph.yaml process.graph.yaml \
  --project-id customer-domain --project-name "Customer Domain" \
  --output customer-domain.graph.yaml
```

The adapters preserve useful semantics instead of flattening the source documents: mapping fields become explicit field/rule traceability; interfaces retain systems, objects, ownership, mapping references, tests, and operational metadata; processes retain steps, transitions, roles, systems, objects, controls, risks, evidence, and interface usage.

## Governance as code

Built-in quality checks catch structural problems. Policy packs add project-specific expectations without hard-coding them into the graph engine.

Supported policy rule primitives in v0.9:

- `forbid_orphan`
- `require_attribute`
- `require_relation`

Rules can target node types, relation direction/type, counterpart node type, minimum relation counts, and severity. The repository includes `enterprise-baseline` and `change-readiness` examples.

```bash
transformation-graph policy graph.yaml \
  --pack policies/enterprise-baseline.yaml \
  --fail-on error
```

## PR/change review

`transformation-graph review` combines semantic graph diff, changed roots, neighboring impact, deterministic review attention, built-in quality delta, and optional policy delta. It emits Markdown for `GITHUB_STEP_SUMMARY` or JSON for automation.

The repository self-tests this pattern in `.github/workflows/pr-graph-review.yml`.

## Agent/MCP use

```bash
transformation-graph context-pack \
  examples/sap-s4-customer-migration.yaml \
  mapping.customer-to-bp --depth 1

transformation-graph mcp examples/sap-s4-customer-migration.yaml
```

The useful AI pattern is not to send the whole project to a model. Resolve the node or change in question, traverse only relevant dependencies, emit a bounded deterministic context pack, let the model reason over explicit relationships, and keep validation, policy checks, and change detection outside the model.

## Why this matters

A field changes. Which mapping reads it? Which interface carries the result? Which process step depends on the interface? Which test covers the change? Which decision introduced the rule? Who owns the decision? Which evidence supports the mapping?

Those questions are usually answered by manually reconciling several tools and documents. Transformation Graph makes those relationships explicit, versionable, queryable, reviewable in Git, and consumable by both people and agents.

Documentation: [model](docs/model.md) · [queries](docs/queries.md) · [quality](docs/quality.md) · [enterprise ingestion](docs/enterprise-ingestion.md) · [policies and PR review](docs/policies-and-review.md) · [change intelligence](docs/change-intelligence.md) · [HTML explorer](docs/html-explorer.md) · [agent context](docs/agent-context.md) · [MCP adapter](docs/mcp.md).

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

**Executable MVP / v0.9.** Authoring, validation, enterprise ingestion, adapter composition, governance policies, query/impact, visualization, semantic change review, deterministic agent context, and MCP access are implemented.
