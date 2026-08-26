from pathlib import Path

from transformation_graph import Graph
from transformation_graph.diffing import diff_with_impact, graph_diff

BEFORE = Path("examples/change/before.yaml")
AFTER = Path("examples/change/after.yaml")


def test_graph_diff_detects_added_and_changed_elements():
    report = graph_diff(Graph.from_file(BEFORE), Graph.from_file(AFTER))
    assert report["summary"] == {
        "nodes_added": 1,
        "nodes_removed": 0,
        "nodes_changed": 1,
        "edges_added": 1,
        "edges_removed": 0,
        "edges_changed": 0,
    }
    assert report["changed_roots"] == ["interface.customer", "system.s4"]
    assert report["nodes"]["added"][0]["id"] == "system.s4"
    assert report["nodes"]["changed"][0]["id"] == "interface.customer"


def test_graph_diff_can_expand_neighboring_impact():
    report = diff_with_impact(Graph.from_file(BEFORE), Graph.from_file(AFTER), depth=1)
    assert [item["id"] for item in report["impact"]["impacted_nodes"]] == ["system.erp", "test.customer"]
