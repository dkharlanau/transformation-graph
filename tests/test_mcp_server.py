import asyncio
from pathlib import Path

from transformation_graph.mcp_server import create_mcp_server

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_mcp_server_registers_bounded_resources_and_tools():
    server = create_mcp_server(EXAMPLE)
    tools = asyncio.run(server.list_tools())
    resources = asyncio.run(server.list_resources())
    templates = asyncio.run(server.list_resource_templates())

    assert {tool.name for tool in tools} == {
        "get_context",
        "find_path",
        "analyze_impact",
        "graph_quality",
        "governance_scorecard",
        "traceability",
        "role_view",
    }
    assert len(resources) == 1
    assert str(resources[0].uri).rstrip("/") == "transformation-graph://project"
    assert len(templates) == 1
    assert str(templates[0].uri_template) == "transformation-graph://context/{node_id}"


def test_mcp_context_resource_returns_existing_context():
    server = create_mcp_server(EXAMPLE)
    contents = asyncio.run(server.read_resource("transformation-graph://context/mapping.customer-to-bp"))
    items = list(contents)
    assert len(items) == 1
    assert "mapping.customer-to-bp" in str(items[0].content)
