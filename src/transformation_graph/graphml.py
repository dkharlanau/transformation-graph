from __future__ import annotations

import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .model import Graph

GRAPHML_NS = "http://graphml.graphdrawing.org/xmlns"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = "http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd"

ET.register_namespace("", GRAPHML_NS)
ET.register_namespace("xsi", XSI_NS)


def _q(name: str) -> str:
    return f"{{{GRAPHML_NS}}}{name}"


def _key(root: ET.Element, key_id: str, domain: str, name: str) -> None:
    ET.SubElement(
        root,
        _q("key"),
        {
            "id": key_id,
            "for": domain,
            "attr.name": name,
            "attr.type": "string",
        },
    )


def _data(parent: ET.Element, key: str, value: object | None) -> None:
    if value is None:
        return
    element = ET.SubElement(parent, _q("data"), {"key": key})
    element.text = str(value)


def render_graphml(graph: Graph) -> str:
    """Render deterministic, standards-oriented GraphML for external graph tooling.

    XML node IDs are generated as n0..nN so arbitrary canonical graph IDs remain
    valid even when they contain characters restricted by GraphML's NMTOKEN IDs.
    The canonical stable ID is retained in node data key ``stable_id``.
    """
    root = ET.Element(
        _q("graphml"),
        {f"{{{XSI_NS}}}schemaLocation": SCHEMA_LOCATION},
    )
    for key_id, domain, name in [
        ("g_project_id", "graph", "project_id"),
        ("g_project_name", "graph", "project_name"),
        ("g_project_description", "graph", "project_description"),
        ("n_stable_id", "node", "stable_id"),
        ("n_type", "node", "type"),
        ("n_title", "node", "title"),
        ("n_description", "node", "description"),
        ("n_tags", "node", "tags_json"),
        ("n_attributes", "node", "attributes_json"),
        ("e_type", "edge", "type"),
        ("e_label", "edge", "label"),
        ("e_attributes", "edge", "attributes_json"),
    ]:
        _key(root, key_id, domain, name)

    graph_element = ET.SubElement(root, _q("graph"), {"id": "G", "edgedefault": "directed"})
    _data(graph_element, "g_project_id", graph.project.get("id"))
    _data(graph_element, "g_project_name", graph.project.get("name"))
    _data(graph_element, "g_project_description", graph.project.get("description"))

    ordered_ids = sorted(graph.nodes)
    aliases = {node_id: f"n{index}" for index, node_id in enumerate(ordered_ids)}
    for node_id in ordered_ids:
        node = graph.nodes[node_id]
        element = ET.SubElement(graph_element, _q("node"), {"id": aliases[node_id]})
        _data(element, "n_stable_id", node.id)
        _data(element, "n_type", node.type)
        _data(element, "n_title", node.title)
        _data(element, "n_description", node.description)
        if node.tags:
            _data(element, "n_tags", json.dumps(list(node.tags), ensure_ascii=False, separators=(",", ":")))
        if node.attributes:
            _data(element, "n_attributes", json.dumps(node.attributes, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    ordered_edges = sorted(
        graph.edges,
        key=lambda edge: (edge.source, edge.target, edge.type, edge.label or "", json.dumps(edge.attributes, sort_keys=True)),
    )
    for index, edge in enumerate(ordered_edges):
        element = ET.SubElement(
            graph_element,
            _q("edge"),
            {"id": f"e{index}", "source": aliases[edge.source], "target": aliases[edge.target]},
        )
        _data(element, "e_type", edge.type)
        _data(element, "e_label", edge.label)
        if edge.attributes:
            _data(element, "e_attributes", json.dumps(edge.attributes, ensure_ascii=False, sort_keys=True, separators=(",", ":")))

    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8") + "\n"


def write_graphml(graph: Graph, output_path: str | Path) -> None:
    Path(output_path).write_text(render_graphml(graph), encoding="utf-8")
