# Enterprise ingestion

Transformation Graph is most useful when teams can start from artifacts they already maintain. v0.8 adds two ingestion paths: generic table inventories and semantic adapters for neighboring as-code formats.

## CSV and Excel inventory contract

CSV and Excel use the same logical columns.

### Nodes

Required columns:

| Column | Meaning |
| --- | --- |
| `id` | Stable graph identifier |
| `type` | Canonical node type or custom `x-*` type |
| `title` | Human-readable title |

Optional columns are `description`, semicolon-separated `tags`, and `attributes_json` containing a JSON object.

### Edges

Required columns are `from`, `to`, and `type`. Optional columns are `label` and `attributes_json`.

Excel workbooks use `Nodes` and `Edges` worksheets by default. Sheet names can be overridden with `--nodes-sheet` and `--edges-sheet`.

```bash
python -m pip install -e ".[excel]"
transformation-graph import-excel inventory.xlsx \
  --project-id s4-program \
  --project-name "S/4 Transformation" \
  --output inventory.graph.yaml
```

The Excel dependency is optional so the core CLI remains lightweight.

## As-code adapters

`import-adapter` converts domain artifacts into the canonical graph while keeping useful semantics.

```bash
transformation-graph import-adapter mapping mapping.yaml --output mapping.graph.yaml
transformation-graph import-adapter interface interface.yaml --output interface.graph.yaml
transformation-graph import-adapter process process.yaml --output process.graph.yaml
```

### Mapping as Code

A mapping becomes a `mapping` node. Source and target objects become `data_object` nodes. Every field mapping creates explicit source/target `field` nodes plus a `rule` node holding the transformation rule. This enables traceability such as mapping → rule → target field without losing object-level mapping relationships.

### Interface as Code

An interface becomes an `interface` node linked to source, target, and middleware `system` nodes; source/target data objects; mapping profile; owners; and tests. Trigger, contract, delivery, retry, monitoring, reconciliation, SLA, security, and profile data are preserved as interface attributes.

### Process as Code

A process becomes a `process` node containing `process_step` nodes. Roles become owners; systems, business objects, interfaces, controls, risks, and evidence become graph entities. Step transitions are explicit `precedes` edges, while step usage links preserve actor, system, object, interface, control, risk, and evidence context.

## Compose artifact slices

Each adapter output remains a normal graph, so independent slices can be composed:

```bash
transformation-graph compose \
  process.graph.yaml interface.graph.yaml mapping.graph.yaml \
  --project-id customer-domain \
  --project-name "Customer Domain" \
  --output customer-domain.graph.yaml
```

Composition is deterministic. Duplicate identical nodes/edges are deduplicated; conflicting definitions of the same node ID fail rather than silently selecting one source.

## Design boundary

Adapters are normalization layers, not source-of-truth replacements. The original process/interface/mapping artifacts remain authoritative for their domain. Transformation Graph provides the connective layer needed for cross-artifact queries, impact analysis, review, and bounded agent context.
