from __future__ import annotations

from pathlib import Path
from typing import Literal

from mcp.server import MCPServer

from .agent_context import build_context_pack
from .governance_views import build_governance_view, VIEW_SPECS
from .model import Graph
from .scorecard import build_scorecard
from .traceability import ROLE_PRESETS, role_traceability, traceability_matrix

Transport = Literal["stdio", "streamable-http"]


def create_mcp_server(graph_path: str | Path) -> MCPServer:
    path = Path(graph_path); graph = Graph.from_file(path); source = str(path)
    mcp = MCPServer("Transformation Graph", instructions="Read project-scoped transformation dependencies. Prefer bounded deterministic graph tools over broad document retrieval.")

    @mcp.resource("transformation-graph://project", mime_type="application/json")
    def project_summary() -> dict: return {"project": dict(graph.project), "stats": graph.stats(), "source": source}

    @mcp.resource("transformation-graph://context/{node_id}", mime_type="application/json")
    def node_context(node_id: str) -> dict: return build_context_pack(graph, node_id, depth=1, source=source)

    @mcp.tool()
    def get_context(node_id: str, depth: int = 1) -> dict: return build_context_pack(graph, node_id, depth=depth, source=source)

    @mcp.tool()
    def find_path(source_node: str, target_node: str, undirected: bool = False) -> dict:
        result = graph.path(source_node, target_node, undirected=undirected)
        return {"found": result is not None, "source": source_node, "target": target_node, "undirected": undirected, "path": result or []}

    @mcp.tool()
    def analyze_impact(node_id: str, depth: int = 2, direction: str = "both") -> dict: return graph.impact(node_id, depth=depth, direction=direction)

    @mcp.tool()
    def graph_quality() -> dict: return graph.quality()

    @mcp.tool()
    def governance_scorecard() -> dict: return build_scorecard(graph)

    @mcp.tool()
    def governance_view(view: str) -> dict:
        """Return ownership, test-coverage, or change-readiness review view."""
        if view not in {*VIEW_SPECS, "change-readiness"}: return {"error": f"unknown governance view: {view}", "available_views": ["ownership", "test-coverage", "change-readiness"]}
        return build_governance_view(graph, view)

    @mcp.tool()
    def traceability(source_type: str, target_type: str, max_depth: int = 4, directed: bool = False) -> dict: return traceability_matrix(graph, {source_type}, {target_type}, max_depth=max_depth, undirected=not directed)

    @mcp.tool()
    def role_view(role: str, max_depth: int = 4) -> dict:
        if role not in ROLE_PRESETS: return {"error": f"unknown role: {role}", "available_roles": sorted(ROLE_PRESETS)}
        return role_traceability(graph, role, max_depth=max_depth)

    return mcp


def run_mcp_server(graph_path: str | Path, transport: Transport = "stdio", host: str = "127.0.0.1", port: int = 8000) -> None:
    mcp = create_mcp_server(graph_path)
    if transport == "stdio": mcp.run()
    else: mcp.run(transport="streamable-http", host=host, port=port)
