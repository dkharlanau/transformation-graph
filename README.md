# Transformation Graph

**Git-native enterprise transformation traceability across processes, systems, data, interfaces, mappings, tests, changes, decisions, ownership, and evidence.**

[![CI](https://github.com/dkharlanau/transformation-graph/actions/workflows/ci.yml/badge.svg)](https://github.com/dkharlanau/transformation-graph/actions/workflows/ci.yml)

Transformation Graph is a lightweight dependency layer for SAP S/4HANA and other enterprise transformation programs. It turns fragmented project knowledge from Excel, architecture diagrams, interface specifications, mapping workbooks, process definitions, test evidence, and change records into one versionable graph that people, CI pipelines, and AI agents can query deterministically.

No SAP system access is required.

## Questions it is designed to answer

- Which mappings and rules depend on this field?
- Which interfaces and systems are downstream of this change?
- Which process steps use the affected interface?
- Which tests cover the requirement or change?
- Which decision or owner governs the rule?
- What changed between two graph snapshots, and what else is impacted?
- Which transformation relationships are missing evidence, ownership, test coverage, or policy-required links?

## Executable capabilities

- canonical YAML/JSON graph model and JSON Schema
- deterministic validation, shortest paths, bounded context, impact traversal, and quality checks
- traceability matrix export to JSON, Markdown, and CSV
- role-oriented views for architect, integration, data, test, and cutover work
- generic CSV and Excel ingestion
- Mapping as Code, Interface as Code, and Process as Code adapters
- semantic adapter conformance and reconciled cross-artifact composition
- configurable governance policy packs with CI failure thresholds
- semantic graph diff and Markdown/JSON change-review reports
- dependency-free HTML explorer with interactive SVG graph canvas
- portable static site bundle with canonical JSON, catalog, manifest, role reports, sitemap, robots metadata, and `llms.txt`
- bounded agent context packs with provenance
- optional MCP v2 server with deterministic context/path/impact/quality/traceability tools
- GitHub Actions CI, PR review, Pages, and tag-driven release workflows

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

## Traceability instead of document hunting

Generate a field-level matrix:

```bash
transformation-graph trace examples/sap-s4-customer-migration.yaml \
  --from-type mapping --to-type field --max-depth 3 \
  --format markdown --output traceability.md
```

Generate a role-oriented view:

```bash
transformation-graph role-view examples/sap-s4-customer-migration.yaml integration \
  --format csv --output integration-traceability.csv

transformation-graph roles
```

Role presets currently cover `architect`, `integration`, `data`, `test`, and `cutover`. The reports contain deterministic shortest paths and coverage gaps; they are not generated narrative summaries.

## Bring enterprise artifacts into the graph

CSV and Excel inventories use `Nodes` and `Edges` contracts. Excel support is optional:

```bash
python -m pip install -e ".[excel]"
transformation-graph import-excel transformation-inventory.xlsx \
  --project-id program --project-name "S/4 Program" \
  --output program.yaml
```

Normalize and conformance-check neighboring as-code artifacts:

```bash
transformation-graph adapter-check mapping examples/adapters/mapping.yaml
transformation-graph adapter-check interface examples/adapters/interface.yaml
transformation-graph adapter-check process examples/adapters/process.yaml
```

Compose them directly without intermediate graph files:

```bash
transformation-graph compose-adapters \
  --mapping examples/adapters/mapping.yaml \
  --interface examples/adapters/interface.yaml \
  --process examples/adapters/process.yaml \
  --project-id customer-domain --project-name "Customer Domain" \
  --output customer-domain.graph.yaml
```

Same-ID nodes are reconciled only when their metadata is compatible. Conflicting attributes stop composition instead of being silently guessed.

## Governance and change review

```bash
transformation-graph policy graph.yaml \
  --pack policies/enterprise-baseline.yaml --fail-on error

transformation-graph review before.yaml after.yaml \
  --impact-depth 2 \
  --policy policies/change-readiness.yaml \
  --output review.md
```

The review combines semantic diff, changed roots, neighboring impact, deterministic attention signals, built-in quality delta, and optional policy delta. `.github/workflows/pr-graph-review.yml` demonstrates the pattern in GitHub Actions.

## Visual and static publishing

Generate one offline explorer:

```bash
transformation-graph html graph.yaml --output explorer.html
```

Generate a portable website:

```bash
transformation-graph site graph.yaml \
  --output _site \
  --base-url https://example.com/transformation-graph/
```

The site contains a human landing page and explorer plus `graph.json`, `catalog.json`, `manifest.json`, `llms.txt`, role-specific HTML/JSON/Markdown/CSV reports, `robots.txt`, and `sitemap.xml`. `.github/workflows/pages.yml` can publish the same bundle to GitHub Pages after GitHub Actions is selected once as the repository's Pages publishing source.

## Agent and MCP use

```bash
transformation-graph context-pack graph.yaml mapping.customer-to-bp --depth 1
python -m pip install -e ".[mcp]"
transformation-graph mcp graph.yaml
```

The useful AI pattern is bounded retrieval over explicit relationships: resolve a stable node, traverse only relevant dependencies, and keep validation, policy checks, graph diff, and traceability deterministic outside the language model.

## Build and release readiness

```bash
python -m build
```

CI verifies wheel and source-distribution builds. A pushed tag such as `v0.13.0` triggers `.github/workflows/release.yml`, which verifies that tag and package versions match and creates a GitHub Release with distribution files and SHA-256 checksums. PyPI publishing is intentionally not enabled yet.

## Documentation

[Model](docs/model.md) · [Queries](docs/queries.md) · [Quality](docs/quality.md) · [Enterprise ingestion](docs/enterprise-ingestion.md) · [Policies and PR review](docs/policies-and-review.md) · [Change intelligence](docs/change-intelligence.md) · [HTML explorer](docs/html-explorer.md) · [Agent context](docs/agent-context.md) · [MCP](docs/mcp.md) · [Releasing](docs/releasing.md)

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

**Executable alpha / v0.13.** The core graph, enterprise ingestion, adapter conformance/composition, governance, traceability, impact/change review, visual/static publishing, bounded agent context, MCP access, CI, and release build path are implemented.
