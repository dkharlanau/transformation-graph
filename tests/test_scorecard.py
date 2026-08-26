from pathlib import Path

from transformation_graph import Graph
from transformation_graph.scorecard import build_scorecard, render_scorecard_markdown

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_scorecard_is_transparent_and_bounded():
    report = build_scorecard(Graph.from_file(EXAMPLE))

    assert 0 <= report["score"] <= 100
    assert report["applicable_weight"] > 0
    connectivity = next(item for item in report["dimensions"] if item["id"] == "connectivity")
    assert connectivity["percentage"] == 100.0
    assert all("numerator" in item and "denominator" in item for item in report["dimensions"])


def test_scorecard_exposes_orphan_gap():
    graph = Graph(
        {
            "version": "0.1",
            "project": {"id": "gap", "name": "Gap"},
            "nodes": [
                {"id": "system.a", "type": "system", "title": "A"},
                {"id": "system.b", "type": "system", "title": "B"},
                {"id": "interface.i", "type": "interface", "title": "I"},
            ],
            "edges": [{"from": "system.a", "to": "interface.i", "type": "sends_via"}],
        }
    )
    report = build_scorecard(graph)
    connectivity = next(item for item in report["dimensions"] if item["id"] == "connectivity")
    assert connectivity["percentage"] < 100
    assert {gap["id"] for gap in connectivity["gaps"]} == {"system.b"}
    assert "system.b" in render_scorecard_markdown(report)
