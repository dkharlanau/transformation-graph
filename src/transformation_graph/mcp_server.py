from __future__ import annotations

from pathlib import Path
from typing import Literal

from mcp.server import MCPServer

from .agent_context import build_context_pack
from .model import Graph
from .traceability import ROLE_PRESETS, role_traceability, traceability_matrix

Transport = Literal["stdio", "streamable-http"]


def create_mcp_server(graph_path: str | Path) -> MCPServer:
    """Create an MCP server backed by one validated Transformation Graph file."""
    path = Path(graph_path)
    graph = Graph.from_file(path)
    source = str(path)

    mcp = MCPServer(
        "Transformation Graph",
        instructions=(
            "Read project-scoped transformation dependencies. Prefer bounded context resources "
            "and deterministic graph tools over broad document retrieval."
        ),
    )

    @mcp.resource("transformation-graph://project", mime_type="application/json")
    def project_summary() -> dict:
        """Project metadata and graph inventory."""
        return {"project": dict(graph.project), "stats": graph.stats(), "source": source}

    @mcp.resource("transformation-graph://context/{node_id}", mime_type="application/json")
    def node_context(node_id: str) -> dict:
        """Depth-1 deterministic context pack around a stable graph node ID."""
        return build_context_pack(graph, node_id, depth=1, source=source)

    @mcp.tool()
    def get_context(node_id: str, depth: int = 1) -> dict:
        """Return a bounded deterministic context pack around a graph node."""
        return build_context_pack(graph, node_id, depth=depth, source=source)

    @mcp.tool()
    def find_path(source_node: str, target_node: str, undirected: bool = False) -> dict:
        """Find the shortest dependency path between two graph nodes."""
        result = graph.path(source_node, target_node, undirected=undirected)
        return {
            "found": result is not None,
            "source": source_node,
            "target": target_node,
            "undirected": undirected,
            "path": result or [],
        }

    @mcp.tool()
    def analyze_impact(node_id: str, depth: int = 2, direction: str = "both") -> dict:
        """Traverse graph impact around a node using in, out, or both directions."""
        return graph.impact(node_id, depth=depth, direction=direction)

    @mcp.tool()
    def graph_quality() -> dict:
        """Return deterministic orphan, coverage, evidence, and ownership findings."""
        return graph.quality()

    @mcp.tool()
    def traceability(source_type: str, target_type: str, max_depth: int = 4, directed: bool = False) -> dict:
        """Build shortest-path traceability between two node types."""
        return traceability_matrix(
            graph,
            {source_type},
            {target_type},
            max_depth=max_depth,
            undirected=not directed,
        )

    @mcp.tool()
    def role_view(role: str, max_depth: int = 4) -> dict:
        """Return a built-in role-oriented traceability view."""
        if role not in ROLE_PRESETS:
            return {
                "error": f"unknown role: {role}",
                "available_roles": sorted(ROLE_PRESETS),
            }
        return role_traceability(graph, role, max_depth=max_depth)

    return mcp


def run_mcp_server(
    graph_path: str | Path,
    transport: Transport = "stdio",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Run the graph MCP server over stdio or Streamable HTTP."""
    mcp = create_mcp_server(graph_path)
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="streamable-http", host=host, port=port)
