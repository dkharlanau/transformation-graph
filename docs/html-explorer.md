# Static HTML explorer

Transformation Graph can generate a self-contained HTML explorer with no runtime server and no external JavaScript/CSS dependencies.

```bash
transformation-graph html \
  examples/sap-s4-customer-migration.yaml \
  --output transformation-graph.html
```

Open the generated file in a browser. It provides project statistics, node search, node-type filtering, node attributes, and direct incoming/outgoing relationships.

A custom page title is optional:

```bash
transformation-graph html project.yaml --output project.html --title "S/4 Transformation Graph"
```

## Why single-file output?

- easy to attach to a project artifact or release
- works offline
- safe to regenerate in CI
- can be hosted later as a static project page
- keeps the canonical YAML/JSON graph as the source of truth

The explorer is a generated view, not a second database. Recreate it from the graph whenever the model changes.
