# Transformation Graph

**A Git-native connective layer for enterprise transformations.**

Transformation Graph links processes, systems, business objects, data, fields, interfaces, mappings, rules, requirements, tests, changes, decisions, owners, and evidence in one project-scoped graph.

## What is executable today

- canonical YAML/JSON graph model and JSON Schema
- deterministic semantic validation
- realistic SAP S/4HANA customer migration example
- dependency paths, impact traversal, and quality checks
- Mermaid export and dependency-free HTML explorer
- generic CSV import and deterministic graph composition
- semantic graph diff and neighboring change-impact
- stable bounded context-pack contract
- optional MCP v2 server exposing graph resources and deterministic tools
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

Agent/MCP use:

```bash
transformation-graph context-pack examples/sap-s4-customer-migration.yaml mapping.customer-to-bp --depth 1
transformation-graph mcp examples/sap-s4-customer-migration.yaml
```

Generated view and change review:

```bash
transformation-graph html examples/sap-s4-customer-migration.yaml --output transformation-graph.html
transformation-graph diff examples/change/before.yaml examples/change/after.yaml --impact-depth 1
```

Import and compose existing inventories:

```bash
transformation-graph import-csv --nodes nodes.csv --edges edges.csv --project-id demo --project-name "Demo" --output demo.yaml
transformation-graph compose process.yaml data.yaml interfaces.yaml --project-id program --project-name "Program Graph" --output program.yaml
```

## Why this exists

Enterprise transformation knowledge is usually fragmented across architecture slides, Excel mappings, Jira, process documents, test evidence, and people's heads. A field changes: which mapping uses it, which interface moves it, which test covers it, which decision created the rule, and which process is affected? Transformation Graph creates the missing cross-artifact dependency layer.

Documentation: [model](docs/model.md) · [queries](docs/queries.md) · [quality](docs/quality.md) · [import/composition](docs/importing.md) · [change intelligence](docs/change-intelligence.md) · [HTML explorer](docs/html-explorer.md) · [agent context](docs/agent-context.md) · [MCP adapter](docs/mcp.md).

## Agent-ready by design

The useful AI pattern is not to send the whole project to a model. Resolve the node or change in question, traverse only relevant dependencies, emit a bounded deterministic context pack, let the model reason over explicit relationships, and keep validation/change detection outside the model. The MCP adapter exposes the same contract rather than inventing a second agent-specific data model.

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

**Executable MVP / v0.7.** Authoring, validation, query, import, composition, visualization, quality analysis, semantic change review, deterministic agent context, and MCP access are implemented.
