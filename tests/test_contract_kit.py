import json
from pathlib import Path

from transformation_graph.adapters import graph_from_as_code
from transformation_graph.conformance import evaluate_adapter_graph
from transformation_graph.contracts import ADAPTER_CONTRACT_ID, ADAPTER_CONTRACT_VERSION

KIT = Path("conformance/adapter-v0.1")


def test_versioned_contract_catalog_fixtures_are_conformant():
    catalog = json.loads((KIT / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["contract"] == {
        "id": ADAPTER_CONTRACT_ID,
        "version": ADAPTER_CONTRACT_VERSION,
        "canonical_graph_version": "0.1",
    }
    for fixture in catalog["fixtures"]:
        graph = graph_from_as_code(KIT / fixture["path"], fixture["kind"])
        report = evaluate_adapter_graph(graph, fixture["kind"])
        assert report["contract"]["version"] == ADAPTER_CONTRACT_VERSION
        assert report["summary"]["errors"] == fixture["expected"]["errors"]
        assert report["passed"] is True


def test_conformance_report_schema_declares_contract_identity():
    schema = json.loads(Path("schema/adapter-conformance-report.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["contract"]["properties"]["id"]["const"] == ADAPTER_CONTRACT_ID
