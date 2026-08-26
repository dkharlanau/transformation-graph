from pathlib import Path
import pytest, yaml
from transformation_graph import Graph, GraphValidationError
from transformation_graph.importers import graph_from_csv, write_graph

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")

def test_example_is_valid_and_has_expected_shape():
    graph = Graph.from_file(EXAMPLE); stats = graph.stats(); assert stats["project"] == "customer-master-migration"; assert stats["nodes"] == 20; assert stats["edges"] == 25; assert stats["node_types"]["mapping"] == 1; assert stats["node_types"]["system"] == 2

def test_directed_path_connects_change_to_rule():
    assert Graph.from_file(EXAMPLE).path("change.bp-model", "rule.id-conversion") == ["change.bp-model","decision.external-number","rule.id-conversion"]

def test_undirected_path_supports_impact_navigation():
    result = Graph.from_file(EXAMPLE).path("evidence.mapping-workbook", "system.s4", undirected=True); assert result and result[0] == "evidence.mapping-workbook" and result[-1] == "system.s4"

def test_context_is_bounded_and_contains_neighbors():
    ids = {node["id"] for node in Graph.from_file(EXAMPLE).context("mapping.customer-to-bp",1)["nodes"]}; assert {"mapping.customer-to-bp","field.kunnr","field.bp-id","rule.id-conversion","evidence.mapping-workbook"} <= ids

def test_dangling_edge_is_rejected(tmp_path):
    payload={"version":"0.1","project":{"id":"broken","name":"Broken"},"nodes":[{"id":"system.a","type":"system","title":"A"}],"edges":[{"from":"system.a","to":"system.missing","type":"depends_on"}]}; path=tmp_path/"broken.yaml"; path.write_text(yaml.safe_dump(payload),encoding="utf-8")
    with pytest.raises(GraphValidationError,match="unknown node"): Graph.from_file(path)

def test_custom_node_type_requires_extension_prefix():
    payload={"version":"0.1","project":{"id":"custom","name":"Custom"},"nodes":[{"id":"custom.1","type":"cutover_task","title":"Task"}],"edges":[]}
    with pytest.raises(GraphValidationError,match="custom types must start with 'x-'"): Graph(payload)

def test_quality_report_passes_for_reference_example():
    report=Graph.from_file(EXAMPLE).quality(); assert report["passed"] is True; assert report["summary"] == {"errors":0,"warnings":0,"findings":0}

def test_impact_can_be_filtered_by_relation():
    result=Graph.from_file(EXAMPLE).impact("change.bp-model",1,"out",{"covered_by"}); assert [item["id"] for item in result["impacted_nodes"]] == ["test.customer-load"]

def test_mermaid_focus_exports_bounded_subgraph():
    diagram=Graph.from_file(EXAMPLE).mermaid("mapping.customer-to-bp",1); assert diagram.startswith("graph LR"); assert "Customer to Business Partner mapping (mapping)" in diagram; assert "SAP S/4HANA (system)" not in diagram

def test_compose_merges_valid_graphs():
    shared={"id":"system.shared","type":"system","title":"Shared"}; left=Graph({"version":"0.1","project":{"id":"left","name":"Left"},"nodes":[shared,{"id":"system.left","type":"system","title":"Left"}],"edges":[{"from":"system.left","to":"system.shared","type":"sends_to"}]}); right=Graph({"version":"0.1","project":{"id":"right","name":"Right"},"nodes":[shared,{"id":"system.right","type":"system","title":"Right"}],"edges":[{"from":"system.shared","to":"system.right","type":"sends_to"}]}); combined=Graph.compose([left,right],"combined","Combined"); assert combined.stats()["nodes"]==3; assert combined.stats()["edges"]==2; assert combined.project["sources"]==["left","right"]

def test_compose_rejects_conflicting_shared_node():
    left=Graph({"version":"0.1","project":{"id":"left","name":"Left"},"nodes":[{"id":"system.shared","type":"system","title":"Shared A"}],"edges":[]}); right=Graph({"version":"0.1","project":{"id":"right","name":"Right"},"nodes":[{"id":"system.shared","type":"system","title":"Shared B"}],"edges":[]})
    with pytest.raises(GraphValidationError,match="conflicting node"): Graph.compose([left,right],"combined","Combined")

def test_csv_import_and_write_round_trip(tmp_path):
    graph=graph_from_csv("examples/csv/nodes.csv","examples/csv/edges.csv","csv-example","CSV Example"); output=tmp_path/"graph.yaml"; write_graph(graph,output); loaded=Graph.from_file(output); assert loaded.stats()["nodes"]==4; assert loaded.stats()["edges"]==3; assert loaded.nodes["system.source"].attributes["product"]=="SAP ERP"; assert loaded.nodes["system.source"].tags==("sap","source")
