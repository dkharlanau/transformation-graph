from pathlib import Path

import pytest
import yaml

from transformation_graph import Graph, GraphValidationError

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_example_is_valid_and_has_expected_shape():
    graph = Graph.from_file(EXAMPLE); stats = graph.stats()
    assert stats["project"] == "customer-master-migration"
    assert stats["nodes"] == 20
    assert stats["edges"] == 25
    assert stats["node_types"]["mapping"] == 1
    assert stats["node_types"]["system"] == 2


def test_directed_path_connects_change_to_rule():
    graph = Graph.from_file(EXAMPLE)
    assert graph.path("change.bp-model", "rule.id-conversion") == ["change.bp-model", "decision.external-number", "rule.id-conversion"]


def test_undirected_path_supports_impact_navigation():
    graph = Graph.from_file(EXAMPLE); result = graph.path("evidence.mapping-workbook", "system.s4", undirected=True)
    assert result is not None and result[0] == "evidence.mapping-workbook" and result[-1] == "system.s4"


def test_context_is_bounded_and_contains_neighbors():
    graph = Graph.from_file(EXAMPLE); context = graph.context("mapping.customer-to-bp", depth=1); ids = {node["id"] for node in context["nodes"]}
    assert {"mapping.customer-to-bp", "field.kunnr", "field.bp-id", "rule.id-conversion", "evidence.mapping-workbook"} <= ids


def test_dangling_edge_is_rejected(tmp_path):
    payload = {"version": "0.1", "project": {"id": "broken", "name": "Broken"}, "nodes": [{"id": "system.a", "type": "system", "title": "A"}], "edges": [{"from": "system.a", "to": "system.missing", "type": "depends_on"}]}
    path = tmp_path / "broken.yaml"; path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(GraphValidationError, match="unknown node"): Graph.from_file(path)


def test_custom_node_type_requires_extension_prefix():
    payload = {"version": "0.1", "project": {"id": "custom", "name": "Custom"}, "nodes": [{"id": "custom.1", "type": "cutover_task", "title": "Task"}], "edges": []}
    with pytest.raises(GraphValidationError, match="custom types must start with 'x-'"): Graph(payload)


def test_quality_report_passes_for_reference_example():
    graph = Graph.from_file(EXAMPLE); report = graph.quality()
    assert report["passed"] is True
    assert report["summary"] == {"errors": 0, "warnings": 0, "findings": 0}


def test_impact_can_be_filtered_by_relation():
    graph = Graph.from_file(EXAMPLE)
    result = graph.impact("change.bp-model", depth=1, direction="out", relations={"covered_by"})
    assert [item["id"] for item in result["impacted_nodes"]] == ["test.customer-load"]


def test_mermaid_focus_exports_bounded_subgraph():
    graph = Graph.from_file(EXAMPLE); diagram = graph.mermaid(focus="mapping.customer-to-bp", depth=1)
    assert diagram.startswith("graph LR")
    assert "Customer to Business Partner mapping (mapping)" in diagram
    assert "SAP S/4HANA (system)" not in diagram
