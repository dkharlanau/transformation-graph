# Agent context packs

Transformation Graph should give agents explicit, bounded project context rather than dumping an entire transformation repository into a prompt.

## Generate a context pack

```bash
transformation-graph context-pack \
  examples/sap-s4-customer-migration.yaml \
  mapping.customer-to-bp \
  --depth 1 \
  --output mapping-context.json
```

Without `--output`, the packet is printed as JSON.

## Stable packet contract

The v0.1 context-pack contains:

- `format` and packet `version`
- project metadata
- root/depth query
- canonical root node
- graph inventory statistics
- bounded nodes and edges
- quality findings relevant to selected nodes
- provenance source path

The packet deliberately contains no generation timestamp, random ID, or model-generated summary, so the same graph/query produces deterministic output suitable for caching, CI, agent tools, and reproducible investigations.

See `schema/context-pack.schema.json` for the machine-readable contract.

## Intended integration pattern

1. Resolve a stable graph node from the user's question or workflow event.
2. Generate a small context pack at an appropriate depth.
3. Provide that packet to the model or agent as structured evidence.
4. Let deterministic graph validation, quality checks, and change detection remain outside the model.
5. Preserve provenance so agent output can point back to the source graph.

A future MCP adapter can expose the same context-pack contract as a resource without changing the canonical graph model.
