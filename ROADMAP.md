# Roadmap

## v0.1 — Executable core — implemented
- [x] Canonical graph format and JSON Schema
- [x] YAML/JSON loader and semantic validation
- [x] SAP S/4HANA example
- [x] Stats, path, bounded context
- [x] Tests and CI

## v0.2 — Quality and impact — implemented
- [x] Orphan and coverage checks
- [x] Impact traversal by relation and direction
- [x] Machine-readable quality report
- [x] Mermaid export
- [x] Configurable policy packs

## v0.3 — Import and composition — implemented
- [x] CSV importer
- [x] Excel importer
- [x] Compose multiple graph files
- [x] Mapping as Code adapter
- [x] Interface as Code adapter
- [x] Process as Code adapter

## v0.4 — Change intelligence — implemented
- [x] Semantic graph diff between snapshots
- [x] Changed roots and neighboring impact
- [x] Markdown/JSON GitHub PR review summary
- [ ] Optional PR comment/check annotation action

## v0.5 — Generated views — in progress
- [x] Dependency-free static HTML explorer
- [x] Search, type filter, node detail, direct relations
- [x] Interactive SVG dependency graph canvas
- [ ] Dedicated impact and traceability views
- [ ] GitHub Pages publishing workflow

## v0.6 — Agent context — implemented
- [x] Stable JSON context-pack format and schema
- [x] Bounded context with provenance
- [x] Relevant quality findings in agent context

## v0.7 — MCP adapter — implemented
- [x] Official MCP Python SDK v2 adapter
- [x] Project and bounded-context resources
- [x] Context/path/impact/quality tools
- [x] stdio transport
- [x] Streamable HTTP transport
- [ ] Authentication/deployment profile
- [ ] Query presets for transformation roles

## v0.8 — Enterprise ingestion — implemented
- [x] Excel workbook contract compatible with CSV inventories
- [x] Field-level mapping normalization
- [x] Interface operational-context normalization
- [x] Process step/transition/control/evidence normalization

## v0.9 — Governance and review — implemented
- [x] Generic policy-pack engine
- [x] Error/warning CI thresholds
- [x] Change-review report with impact and quality/policy deltas
- [x] Self-dogfooded pull-request summary workflow

## Next
- [ ] Adapter contract versioning and conformance fixtures across sibling repositories
- [ ] Traceability matrix export
- [ ] Role-oriented query presets: architect, data lead, integration lead, test lead, cutover lead
- [ ] Published package/release workflow
- [ ] GitHub Pages project explorer
