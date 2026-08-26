# MCP adapter

Transformation Graph includes an optional MCP server backed by the official Python MCP SDK v2. The canonical graph remains independent of MCP; install the adapter only where an MCP host is needed.

## Install

```bash
pip install -e ".[mcp]"
```

## Local stdio server

```bash
transformation-graph mcp examples/sap-s4-customer-migration.yaml
```

The server exposes:

### Resources

- `transformation-graph://project` — project metadata and inventory
- `transformation-graph://context/{node_id}` — deterministic depth-1 context pack for a stable node

### Tools

- `get_context(node_id, depth)` — bounded context pack
- `find_path(source_node, target_node, undirected)` — shortest dependency path
- `analyze_impact(node_id, depth, direction)` — dependency impact traversal
- `graph_quality()` — deterministic quality findings

The resource/tool split is deliberate: applications can attach known graph context as MCP resources, while the model can call deterministic query tools when it needs to explore a specific relationship.

## Streamable HTTP

```bash
transformation-graph mcp project.yaml \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000
```

For local desktop/IDE hosts, prefer stdio. Streamable HTTP is available when the server needs to run as a network service. Authentication and public deployment are intentionally out of scope for the first adapter; do not expose an unauthenticated project graph server to an untrusted network.

## Host configuration pattern

An MCP host that launches local stdio servers can use the equivalent of:

```json
{
  "command": "transformation-graph",
  "args": ["mcp", "/absolute/path/to/project.yaml"]
}
```

Exact configuration keys differ by host. The graph path should be explicit and project-scoped.
