from transformation_graph.contracts import (
    ADAPTER_CONTRACT_ID,
    ADAPTER_CONTRACT_VERSION,
    load_adapter_contract,
    render_adapter_contract,
)
from transformation_graph.adapters import graph_from_as_code
from transformation_graph.conformance import evaluate_adapter_graph


def test_packaged_adapter_contract_is_versioned_and_complete():
    contract = load_adapter_contract()
    assert contract["contract"]["id"] == ADAPTER_CONTRACT_ID
    assert contract["contract"]["version"] == ADAPTER_CONTRACT_VERSION
    assert set(contract["adapters"]) == {"mapping", "interface", "process"}
    assert "maps_from" in render_adapter_contract("json")


def test_conformance_report_identifies_contract_version():
    graph = graph_from_as_code("examples/adapters/mapping.yaml", "mapping")
    report = evaluate_adapter_graph(graph, "mapping")
    assert report["contract"] == {"id": ADAPTER_CONTRACT_ID, "version": ADAPTER_CONTRACT_VERSION}
