from pathlib import Path

from transformation_graph.adapters import graph_from_as_code
from transformation_graph.composition import compose_adapter_documents, compose_reconciled
from transformation_graph.conformance import evaluate_adapter_graph, render_conformance_markdown
from transformation_graph.model import Graph

EXAMPLES = Path("examples/adapters")


def test_adapter_examples_pass_semantic_conformance():
    for kind in ("mapping", "interface", "process"):
        graph = graph_from_as_code(EXAMPLES / f"{kind}.yaml", kind)
        report = evaluate_adapter_graph(graph, kind)
        assert report["summary"]["errors"] == 0
        assert report["passed"] is True
        assert "adapter conformance" in render_conformance_markdown(report).lower()


def test_mapping_conformance_detects_missing_target():
    graph = Graph(
        {
            "version": "0.1",
            "project": {"id": "broken", "name": "Broken", "source_format": "mapping-as-code"},
            "nodes": [
                {"id": "mapping.demo", "type": "mapping", "title": "Demo"},
                {"id": "data_object.source", "type": "data_object", "title": "Source"},
            ],
            "edges": [{"from": "mapping.demo", "to": "data_object.source", "type": "maps_from"}],
        }
    )
    report = evaluate_adapter_graph(graph, "mapping")
    codes = {item["code"] for item in report["findings"]}
    assert "MAPPING_TARGET_MISSING" in codes
    assert report["passed"] is False


def test_reconciled_composition_unions_complementary_mapping_metadata():
    mapping = graph_from_as_code(EXAMPLES / "mapping.yaml", "mapping")
    interface = graph_from_as_code(EXAMPLES / "interface.yaml", "interface")
    graph = compose_reconciled([interface, mapping], "composed", "Composed")

    node = graph.nodes["mapping.customer-core"]
    assert node.attributes["source"] == "SAP-MDG.BusinessPartner"
    assert node.attributes["profile"] == "customer-core"
    assert graph.project["composition"] == "reconciled"


def test_compose_adapter_documents_checks_and_composes_all_examples():
    graph, checks = compose_adapter_documents(
        [
            ("process", EXAMPLES / "process.yaml"),
            ("mapping", EXAMPLES / "mapping.yaml"),
            ("interface", EXAMPLES / "interface.yaml"),
        ],
        "program",
        "Program",
    )
    assert len(checks) == 3
    assert all(check["passed"] for check in checks)
    assert "mapping.customer-core" in graph.nodes
    assert "interface.CUSTOMER-MDG-S4-01" in graph.nodes
    assert "process.customer_creation" in graph.nodes
