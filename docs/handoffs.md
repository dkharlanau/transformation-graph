# Handoff contracts

Transformation Graph is a derived analysis layer. A handoff is valid only when the producer format, adapter and consumer purpose are explicit.

## Supported inbound handoffs

| Producer | Mechanism | What is retained |
| --- | --- | --- |
| Mapping as Code | `mapping` project adapter | Mapping, rules, fields, reads/writes and source provenance |
| Interface as Code | `interface` project adapter | Interface, source/target systems, ownership, tests and provenance |
| Process as Code | `process` project adapter | Process, steps, transitions, actors/systems and provenance |
| Canonical graph fragment | `sources.graphs` in a project manifest | Declared nodes/edges and source path |
| CSV or Excel | import commands | Explicitly mapped nodes/edges and source-row provenance |

Adapter conformance runs before reconciled composition. A failure stops the project build; it is not converted into an inferred graph edge.

## Supported outbound handoffs

| Output | Intended consumer | Assurance boundary |
| --- | --- | --- |
| `graph.yaml` / `graph.json` | Transformation Graph CLI, site and custom readers | Point-in-time materialization; imported domain contracts remain authoritative |
| `context-pack` JSON | Bounded agent or reviewer context | Exact local graph neighborhood; not a whole-project evidence pack |
| GraphML | Generic graph tooling | Structural interchange; no policy or evidence acceptance is implied |
| Static site and manifest | Human review and machine discovery | Read-only generated view; not an authoring surface |
| Scorecard and governance views | Project governance review | Transparent derived diagnostics; not a universal quality truth |

## Explicit non-integrations

- Enterprise Change Graph does not currently accept a Transformation Graph build as a native input. Choose ECG directly when the durable object is a specific change/release analysis.
- Project Evidence Graph does not currently import Transformation Graph scorecards, context packs or GraphML as evidence.
- Cutover Graph does not infer executable tasks or checkpoint completion from this graph.

These boundaries prevent a structural export from being presented as semantic acceptance by another product.

## Reproducible reference

```bash
transformation-graph build-project \
  examples/project/transformation-project.yaml \
  --output-dir build \
  --site

transformation-graph validate build/graph.yaml
transformation-graph context-pack build/graph.yaml mapping.customer-core \
  --depth 1 \
  --output build/mapping-context.json
```

The reference is synthetic. Successful conformance and a score of 100 describe this repository's declared example and policies; they do not validate a production transformation.
