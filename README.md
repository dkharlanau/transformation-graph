# Transformation Graph

**Git-native enterprise transformation traceability across processes, systems, data, interfaces, mappings, tests, changes, decisions, ownership, and evidence.**

[![CI](https://github.com/dkharlanau/transformation-graph/actions/workflows/ci.yml/badge.svg)](https://github.com/dkharlanau/transformation-graph/actions/workflows/ci.yml)

Transformation Graph is a lightweight dependency layer for SAP S/4HANA and other enterprise transformation programs. It turns fragmented project knowledge from Excel, architecture diagrams, interface specifications, mapping workbooks, process definitions, test evidence, and change records into one versionable graph that people, CI pipelines, and AI agents can query deterministically.

No SAP system access is required.

## One-command project build

The recommended workflow is a versioned project manifest:

```bash
transformation-graph build-project \
  examples/project/transformation-project.yaml \
  --output-dir build
```

One build normalizes Mapping/Interface/Process-as-Code sources, checks adapter conformance, safely reconciles compatible entities, writes the canonical graph, applies governance policies, calculates a transparent scorecard, and generates the static site. Paths are resolved relative to the manifest, so the project remains portable in Git.

Generated outputs include `graph.yaml`, `build-report.json`, `conformance.json`, `policy.json`, `scorecard.json`, and optionally `site/`.

## What it can answer

- Which mappings and rules depend on this field?
- Which interfaces and systems are downstream of this change?
- Which process steps use the affected interface?
- Which tests cover the requirement or change?
- Which decision or owner governs the rule?
- What changed between graph snapshots and what else is impacted?
- Which transformation relationships are missing ownership, evidence, tests, or other required links?

## Core capabilities

- canonical YAML/JSON model and schema
- deterministic validation, shortest paths, context and impact traversal
- CSV/Excel ingestion plus Mapping/Interface/Process-as-Code adapters
- semantic adapter conformance and fail-loud reconciled composition
- configurable governance policies and transparent governance scorecard
- JSON/Markdown/CSV traceability matrices
- architect, integration, data, test, and cutover role views
- semantic diff and PR/change-review reports
- dependency-free HTML/SVG explorer and portable static site
- canonical graph/catalog/manifest, role reports, scorecard, sitemap and `llms.txt`
- bounded agent context packs and optional MCP v2 server
- CI, Pages, package-build and tag-driven GitHub Release workflows

## Direct graph queries

```bash
transformation-graph validate examples/sap-s4-customer-migration.yaml
transformation-graph impact examples/sap-s4-customer-migration.yaml change.bp-model --depth 2
transformation-graph trace examples/sap-s4-customer-migration.yaml \
  --from-type mapping --to-type field --format markdown
transformation-graph role-view examples/sap-s4-customer-migration.yaml integration --format csv
```

## Governance

```bash
transformation-graph policy graph.yaml \
  --pack policies/enterprise-baseline.yaml --fail-on error

transformation-graph scorecard graph.yaml \
  --format markdown --output scorecard.md --fail-below 70
```

The scorecard is not an opaque rating. Each weighted dimension exposes its numerator, denominator, coverage paths, and gaps in JSON.

## As-code ingestion

```bash
transformation-graph adapter-check mapping examples/adapters/mapping.yaml
transformation-graph adapter-check interface examples/adapters/interface.yaml
transformation-graph adapter-check process examples/adapters/process.yaml

transformation-graph compose-adapters \
  --mapping examples/adapters/mapping.yaml \
  --interface examples/adapters/interface.yaml \
  --process examples/adapters/process.yaml \
  --project-id customer-domain --project-name "Customer Domain" \
  --output customer-domain.graph.yaml
```

Same-ID entities are reconciled only when metadata is compatible. Conflicting attributes stop the build rather than being guessed.

## Change review

```bash
transformation-graph review before.yaml after.yaml \
  --impact-depth 2 \
  --policy policies/change-readiness.yaml \
  --output review.md
```

The report combines semantic diff, changed roots, impact, built-in quality delta, and optional policy delta.

## Static publishing

```bash
transformation-graph site graph.yaml --output _site \
  --base-url https://example.com/transformation-graph/
```

The site includes the interactive graph, governance scorecard, role-specific reports, canonical machine-readable artifacts, `robots.txt`, sitemap, and `llms.txt`. `.github/workflows/pages.yml` builds the same governed reference project through `build-project` and can deploy it to GitHub Pages once GitHub Actions is selected as the repository Pages source.

## Agent / MCP

```bash
transformation-graph context-pack graph.yaml mapping.customer-to-bp --depth 1
python -m pip install -e ".[mcp]"
transformation-graph mcp graph.yaml
```

Agent access reuses the same deterministic graph functions for context, path, impact, quality, governance scorecard, traceability, and role views.

## Build and release

```bash
python -m build
```

CI verifies wheel and source-distribution builds. An exact matching `v*` tag triggers the release workflow, which verifies the package version, builds distributions, generates SHA-256 checksums, and creates a GitHub Release. PyPI publishing remains intentionally disabled until a registry release is explicitly chosen.

## Documentation

[Project manifest](docs/project-manifest.md) · [Model](docs/model.md) · [Queries](docs/queries.md) · [Quality](docs/quality.md) · [Enterprise ingestion](docs/enterprise-ingestion.md) · [Policies and review](docs/policies-and-review.md) · [Agent context](docs/agent-context.md) · [MCP](docs/mcp.md) · [Releasing](docs/releasing.md)

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

**Executable alpha / v0.15.** Canonical modeling, enterprise ingestion, governed project builds, traceability, impact/change review, visual/static publishing, bounded agent access, CI and release readiness are implemented.
