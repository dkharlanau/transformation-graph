# Transformation Graph

**Git-native enterprise transformation traceability across processes, systems, data, interfaces, mappings, tests, changes, decisions, ownership, and evidence.**

[![CI](https://github.com/dkharlanau/transformation-graph/actions/workflows/ci.yml/badge.svg)](https://github.com/dkharlanau/transformation-graph/actions/workflows/ci.yml)

Transformation Graph turns fragmented enterprise transformation artifacts into one versionable dependency graph that people, CI pipelines, graph tools, and AI agents can query deterministically. The reference use case is SAP S/4HANA transformation, but the model and tooling are vendor-neutral.

No SAP system access is required.

## Choose this graph when

Use **Transformation Graph** when the durable object you need is a **materialized project model**: a normalized view across process, interface, mapping, data, ownership, tests and evidence that can be rebuilt, governed, scored, explored and queried throughout a transformation.

Use [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph) instead when the primary object is a **concrete change or release decision** and the question is: what does this change affect, why is something in or out of scope, what regression tests are required, and who must review it?

| Question | Transformation Graph | Enterprise Change Graph |
| --- | --- | --- |
| What is the connected transformation model for this project/revision? | **Primary** | Supporting input |
| Where are ownership, test, evidence or traceability gaps? | **Primary** | Change-specific gaps |
| What does change `CR-142` affect and why? | General graph traversal | **Primary** |
| Why is a target excluded from this change's impact? | Not the main abstraction | **Primary (`why-not`)** |
| What minimum regression scope follows from a release? | Can expose coverage | **Primary** |
| Should upstream Mapping/Interface/Process semantics be authored here? | **No** | **No** |

Both products are derived analysis layers. Neither is a universal enterprise CMDB or a second authoring home for semantics owned by Mapping as Code, Interface as Code, or Process as Code.

## Recommended flow: one project manifest

```bash
transformation-graph build-project \
  examples/project/transformation-project.yaml \
  --output-dir build
```

One build normalizes Mapping/Interface/Process-as-Code sources, checks the versioned adapter contract, reconciles compatible entities, applies policies, calculates a transparent governance scorecard, writes the canonical **materialized project graph for that build**, and optionally publishes a complete static site.

Outputs include `graph.yaml`, `build-report.json`, `conformance.json`, `policy.json`, `scorecard.json`, and `site/`.

## Ownership boundary

Transformation Graph is a **derived analysis layer**, not a replacement authoring system for the contracts it imports.

- Mapping as Code remains the semantic owner of source-to-target transformation intent.
- Interface as Code remains the semantic owner of integration trigger, transport, retry/recovery, monitoring, ownership, and interface-contract semantics.
- Process as Code remains the semantic owner of process steps, transitions, roles, and gates.
- Transformation Graph owns graph-specific analysis annotations, graph governance policy/scorecards, materialized project revisions, and derived views that do not belong in those upstream domain contracts.

“Canonical graph” therefore means canonical **inside one Transformation Graph project/revision after deterministic materialization**. It does not mean a universal enterprise master graph or a second source of truth for imported mappings, interfaces, or processes. When imported domain semantics change, change them in the owning product and rebuild the graph. Detached exports remain point-in-time materializations with provenance.

This boundary is deliberate: references and reproducible projections are preferred to maintaining the same business rule independently in several repositories.

## What it answers

- Which mappings and rules depend on a field?
- Which systems/interfaces/process steps are downstream of a change?
- Which tests cover a requirement, mapping, interface, or change?
- Which owner or decision governs an implementation rule?
- What changed between graph revisions and what else is impacted?
- Where are the ownership, test, evidence, system, and data traceability gaps?

## Current capabilities

- canonical YAML/JSON model, schema, validation, paths, bounded context and impact traversal
- CSV/Excel ingestion and Mapping/Interface/Process-as-Code adapters
- `transformation-graph-adapter/v0.1` semantic contract, immutable conformance fixtures, JSON report schema, and reusable GitHub Action
- fail-loud reconciled cross-artifact composition
- governance policies, transparent weighted scorecard, and focused ownership/test/change-readiness views
- JSON/Markdown/CSV traceability matrices and architect/integration/data/test/cutover role views
- semantic graph diff and PR/change-review reports
- interactive dependency-free SVG explorer and portable static site
- canonical JSON/catalog/manifest, `llms.txt`, sitemap, GraphML, scorecard and governance view artifacts
- optional MCP v2 server reusing the same deterministic query/governance functions
- CI, PR review, Pages, package build and tag-driven GitHub Release workflows

## Core commands

```bash
transformation-graph validate graph.yaml
transformation-graph impact graph.yaml change.bp-model --depth 2
transformation-graph trace graph.yaml --from-type mapping --to-type field --format markdown
transformation-graph role-view graph.yaml integration --format csv
transformation-graph governance-view graph.yaml ownership --format html --output ownership.html
transformation-graph scorecard graph.yaml --format markdown --fail-below 70
transformation-graph graphml graph.yaml --output graph.graphml
```

## As-code compatibility

```bash
transformation-graph adapter-contract --format json
transformation-graph adapter-check mapping mapping.yaml
transformation-graph adapter-check interface interface.yaml
transformation-graph adapter-check process process.yaml
```

The reusable Action exposes the same checker to sibling repositories. See [Adapter contract](docs/adapter-contract.md).

## Static publishing and interoperability

```bash
transformation-graph site graph.yaml --output _site \
  --base-url https://example.com/transformation-graph/
```

The generated site includes the interactive graph, governance scorecard, focused governance views, role reports, canonical JSON, GraphML, `llms.txt`, sitemap and machine-readable manifest. `.github/workflows/pages.yml` builds the governed reference project through the same `build-project` pipeline.

GraphML follows the standard directed `graphml` / `graph` / `node` / `edge` model. Safe XML IDs are generated for interchange while canonical Transformation Graph IDs remain explicit node data.

## Handoff contracts

The strongest supported handoff is inbound: Mapping, Interface and Process-as-Code contracts are normalized through versioned adapters, checked for conformance, and composed with explicit project links. The build report retains which source and adapter produced each materialized node.

The supported outbound surfaces have different purposes:

- `graph.yaml` / site `graph.json` are point-in-time materialized project graphs with provenance;
- `context-pack` is a bounded deterministic payload for an agent or reviewer, validated by `schema/context-pack.schema.json`;
- GraphML is structural interchange for graph tooling;
- the static site is a read-only human and machine publication surface;
- scorecards and governance views are derived diagnostics, not upstream truth or retained audit evidence by themselves.

There is currently **no direct native-format handoff to Enterprise Change Graph or Project Evidence Graph**. Enterprise Change Graph does not import a Transformation Graph project build, and Project Evidence Graph does not treat a scorecard or GraphML export as evidence. See [Handoff contracts](docs/handoffs.md) before describing a downstream integration.

## Agent / MCP

```bash
transformation-graph context-pack graph.yaml mapping.customer-to-bp --depth 1
python -m pip install -e ".[mcp]"
transformation-graph mcp graph.yaml
```

MCP tools cover context, paths, impact, quality, governance scorecard, focused governance views, traceability, and role views. Agent reasoning therefore consumes the same deterministic graph functions used by CLI and CI.

## Build and release

```bash
python -m build
```

CI verifies wheel and sdist creation. An exact matching `v*` tag triggers the release workflow, which checks tag/package version equality, builds distributions, creates SHA-256 checksums, and creates a GitHub Release. PyPI publishing remains intentionally disabled until a registry release is explicitly chosen.

## Documentation

[Project manifest](docs/project-manifest.md) · [Adapter contract](docs/adapter-contract.md) · [Handoff contracts](docs/handoffs.md) · [Model](docs/model.md) · [Queries](docs/queries.md) · [Enterprise ingestion](docs/enterprise-ingestion.md) · [Policies and review](docs/policies-and-review.md) · [Agent context](docs/agent-context.md) · [MCP](docs/mcp.md) · [Releasing](docs/releasing.md)

The [public project site](https://dkharlanau.github.io/transformation-graph/) publishes the governed synthetic reference build. Its [explorer](https://dkharlanau.github.io/transformation-graph/explorer/) includes the graph, governance scorecard, focused views, role reports, catalog, GraphML, and machine-readable manifest generated by `build-project`; it is demonstration data, not a production transformation.

## Related projects

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code), [Interface as Code](https://github.com/dkharlanau/interface-as-code), and [Process as Code](https://github.com/dkharlanau/process-as-code) are supported semantic inputs through the versioned adapter contract; each remains authoritative for its domain.
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code) is represented through explicit project graph fragments and links, not through an inferred or automatic evidence import.
- [Enterprise Change Graph](https://github.com/dkharlanau/enterprise-change-graph) owns change-specific propagation, why-not analysis, regression scope and release review. No direct native-format adapter currently connects the two graph products.
- [Project Evidence Graph](https://github.com/dkharlanau/project-evidence-graph) owns retained project assurance. Transformation Graph currently publishes traceability and governance views, not Project Evidence fragments.

Portfolio map: https://dkharlanau.github.io/products/

## Status

**Executable alpha / v0.19.** Governed project builds, cross-repository adapter conformance, traceability/impact/change intelligence, visual/static publishing, GraphML interoperability, bounded agent access, CI and release readiness are implemented.

## About the author

Created and maintained by **Dzmitryi Kharlanau**, an SAP consultant and system analyst working across enterprise architecture, data, integration, operations, and practical AI.

- [Website and knowledge base](https://dkharlanau.github.io/)
- [LinkedIn](https://www.linkedin.com/in/dkharlanau/)
