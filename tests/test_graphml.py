from pathlib import Path
import xml.etree.ElementTree as ET

from transformation_graph import Graph
from transformation_graph.graphml import GRAPHML_NS, render_graphml, write_graphml

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_graphml_is_directed_and_preserves_stable_ids():
    graph = Graph.from_file(EXAMPLE)
    xml = render_graphml(graph)
    root = ET.fromstring(xml)
    ns = {"g": GRAPHML_NS}
    graph_element = root.find("g:graph", ns)
    assert graph_element is not None
    assert graph_element.attrib["edgedefault"] == "directed"
    nodes = root.findall(".//g:node", ns)
    edges = root.findall(".//g:edge", ns)
    assert len(nodes) == graph.stats()["nodes"]
    assert len(edges) == graph.stats()["edges"]
    stable_ids = {
        data.text
        for node in nodes
        for data in node.findall("g:data", ns)
        if data.attrib.get("key") == "n_stable_id"
    }
    assert "mapping.customer-to-bp" in stable_ids
    xml_node_ids = {node.attrib["id"] for node in nodes}
    assert all(edge.attrib["source"] in xml_node_ids and edge.attrib["target"] in xml_node_ids for edge in edges)


def test_graphml_writes_file(tmp_path):
    output = tmp_path / "graph.graphml"
    write_graphml(Graph.from_file(EXAMPLE), output)
    assert output.read_text(encoding="utf-8").startswith("<?xml")
