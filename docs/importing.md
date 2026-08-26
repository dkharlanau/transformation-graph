# Import and composition

Most enterprise transformation projects already have inventories in Excel or CSV. Transformation Graph treats tabular import as a first-class on-ramp rather than requiring teams to hand-author YAML.

## Generic CSV import

```bash
transformation-graph import-csv \
  --nodes examples/csv/nodes.csv \
  --edges examples/csv/edges.csv \
  --project-id integration-slice \
  --project-name "Integration Slice" \
  --output integration-slice.yaml
```

Node CSV requires `id`, `type`, `title`. Optional columns are `description`, semicolon-separated `tags`, and `attributes_json` containing a JSON object. Edge CSV requires `from`, `to`, `type`; optional columns are `label` and `attributes_json`.

The generated graph is validated immediately. Dangling endpoints, duplicate nodes, invalid types, or malformed JSON attributes fail before output is written.

## Compose graph slices

```bash
transformation-graph compose \
  customer.yaml integrations.yaml testing.yaml \
  --project-id program-graph \
  --project-name "Program Transformation Graph" \
  --output program.yaml
```

Composition rules are deterministic: identical shared nodes are deduplicated, conflicting definitions for the same node ID fail, exact duplicate edges are deduplicated, output is sorted, and source project IDs are recorded in `project.sources`.

This supports a future architecture where Mapping as Code, Interface as Code, Process as Code, and other repositories emit graph slices that are composed into a project-wide view.
