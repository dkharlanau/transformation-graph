from pathlib import Path
import json

from transformation_graph import Graph
from transformation_graph.agent_context import build_context_pack, write_context_pack

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_context_pack_is_bounded_deterministic_and_has_provenance():
    graph = Graph.from_file(EXAMPLE)
    first = build_context_pack(graph, "mapping.customer-to-bp", depth=1, source=str(EXAMPLE))
    second = build_context_pack(graph, "mapping.customer-to-bp", depth=1, source=str(EXAMPLE))
    assert first == second
    assert first["format"] == "transformation-graph/context-pack"
    assert first["version"] == "0.1"
    assert first["root"]["id"] == "mapping.customer-to-bp"
    assert first["provenance"]["source"] == str(EXAMPLE)
    ids = {node["id"] for node in first["context"]["nodes"]}
    assert "mapping.customer-to-bp" in ids
    assert "system.s4" not in ids


def test_context_pack_writes_valid_json(tmp_path):
    pack = build_context_pack(Graph.from_file(EXAMPLE), "change.bp-model", depth=1, source="project.yaml")
    output = tmp_path / "context.json"
    write_context_pack(pack, output)
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["query"] == {"root": "change.bp-model", "depth": 1}
    assert loaded["provenance"] == {"source": "project.yaml"}
