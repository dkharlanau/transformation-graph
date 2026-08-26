# Roadmap

## v0.1–v0.9 — Foundation — implemented

- canonical graph format, schema, YAML/JSON loader, validation, stats, paths, context
- quality checks, impact traversal, Mermaid, configurable policy packs
- CSV/Excel import, graph composition, Mapping/Interface/Process-as-Code adapters
- semantic diff, neighboring change impact, PR review reports
- HTML explorer and interactive SVG dependency canvas
- bounded agent context and MCP v2 server
- governance policy engine and CI thresholds

## v0.10 — Traceability and role views — implemented

- [x] JSON/Markdown/CSV traceability matrix
- [x] deterministic relation-aware shortest paths
- [x] architect role view
- [x] integration role view
- [x] data role view
- [x] test role view
- [x] cutover role view
- [x] MCP traceability and role-view tools

## v0.11 — Adapter conformance — implemented

- [x] Mapping-as-Code semantic conformance
- [x] Interface-as-Code semantic conformance
- [x] Process-as-Code semantic conformance and reachability checks
- [x] fail-on error/warning thresholds
- [x] reconciled same-ID composition for compatible adapter metadata
- [x] direct normalize → conformance → compose CLI flow

## v0.12 — Static publishing — implemented

- [x] portable static site bundle
- [x] human landing page and SVG explorer
- [x] canonical graph/catalog/manifest artifacts
- [x] role reports in HTML/JSON/Markdown/CSV
- [x] `llms.txt`, sitemap, robots, `.nojekyll`
- [x] GitHub Pages deployment workflow
- [ ] enable GitHub Actions as Pages publishing source and perform first deployment

## v0.13 — Release readiness — implemented

- [x] wheel + source-distribution build verification
- [x] package discovery metadata and project URLs
- [x] synchronized public/distribution version test
- [x] tag/version verification
- [x] tag-driven GitHub Release workflow
- [x] SHA-256 release checksums
- [x] changelog and release runbook
- [ ] create first intentional public tag/release
- [ ] decide whether/when to enable PyPI trusted publishing

## Next high-value work

- [ ] versioned adapter contracts and conformance fixtures shared with sibling repositories
- [ ] graph coverage/traceability scorecards for program governance
- [ ] dedicated change, test coverage, and ownership views in the site
- [ ] generic GraphML export and optional graph-database adapters
- [ ] PR comment/check annotations in addition to Actions Summary
- [ ] MCP authentication/deployment profile for remote project graphs
- [ ] larger multi-domain reference transformation composed from sibling as-code projects
