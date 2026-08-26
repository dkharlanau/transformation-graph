# Agent instructions

Transformation Graph composes existing contracts into a canonical dependency graph. Source contracts remain authoritative; a graph edge must come from declared data or supported reconciliation, never from plausible inference.

## Working loop

1. Read `README.md`, the project manifest, adapter contract, and `docs/agent-manifest.json`.
2. Build and validate the graph before querying it.
3. Resolve exact node IDs before impact or trace operations.
4. Prefer bounded `context-pack`, path, trace, and impact queries for agent context.
5. Report the concrete path or graph entities behind every impact statement.
6. When an adapter/conformance check fails, stop composition and surface the incompatibility.

## Guardrails

- Do not invent nodes or edges to make the graph look complete.
- Do not rewrite source Process/Interface/Mapping contracts from the normalized graph unless explicitly requested and semantically safe.
- Preserve canonical IDs and deterministic ordering.
- Treat governance scorecards as transparent diagnostics, not opaque truth scores.
- Keep generated build/site artifacts separate from hand-authored manifests and contracts.

## Useful commands

```bash
transformation-graph build-project examples/project/transformation-project.yaml --output-dir build
transformation-graph validate graph.yaml
transformation-graph impact graph.yaml <node-id> --depth 2
transformation-graph context-pack graph.yaml <node-id> --depth 1
transformation-graph mcp graph.yaml
```
