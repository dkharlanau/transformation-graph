from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import json
import yaml

from .model import Graph, GraphValidationError

def _attributes(value: str | None, location: str) -> dict[str, Any]:
    if not value: return {}
    try: parsed = json.loads(value)
    except json.JSONDecodeError as exc: raise GraphValidationError(f"{location} attributes_json is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict): raise GraphValidationError(f"{location} attributes_json must contain a JSON object")
    return parsed

def graph_from_csv(nodes_path: str | Path, edges_path: str | Path, project_id: str, project_name: str, description: str | None = None) -> Graph:
    nodes_path = Path(nodes_path); edges_path = Path(edges_path); nodes: list[dict[str, Any]] = []
    with nodes_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle); missing = {"id","type","title"} - set(reader.fieldnames or [])
        if missing: raise GraphValidationError(f"{nodes_path} missing required columns: {', '.join(sorted(missing))}")
        for line, row in enumerate(reader, start=2):
            node: dict[str, Any] = {"id": (row.get("id") or "").strip(), "type": (row.get("type") or "").strip(), "title": (row.get("title") or "").strip()}
            if (row.get("description") or "").strip(): node["description"] = (row.get("description") or "").strip()
            if (row.get("tags") or "").strip(): node["tags"] = [tag.strip() for tag in (row.get("tags") or "").split(";") if tag.strip()]
            attributes = _attributes(row.get("attributes_json"), f"{nodes_path}:{line}")
            if attributes: node["attributes"] = attributes
            nodes.append(node)
    edges: list[dict[str, Any]] = []
    with edges_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle); missing = {"from","to","type"} - set(reader.fieldnames or [])
        if missing: raise GraphValidationError(f"{edges_path} missing required columns: {', '.join(sorted(missing))}")
        for line, row in enumerate(reader, start=2):
            edge: dict[str, Any] = {"from": (row.get("from") or "").strip(), "to": (row.get("to") or "").strip(), "type": (row.get("type") or "").strip()}
            if (row.get("label") or "").strip(): edge["label"] = (row.get("label") or "").strip()
            attributes = _attributes(row.get("attributes_json"), f"{edges_path}:{line}")
            if attributes: edge["attributes"] = attributes
            edges.append(edge)
    project: dict[str, Any] = {"id": project_id, "name": project_name}
    if description: project["description"] = description
    return Graph({"version":"0.1","project":project,"nodes":nodes,"edges":edges})

def write_graph(graph: Graph, output_path: str | Path) -> None:
    output_path = Path(output_path); payload = graph.as_dict()
    if output_path.suffix.lower() in {".yaml", ".yml"}: output_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"); return
    if output_path.suffix.lower() == ".json": output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"); return
    raise GraphValidationError("output file must end with .yaml, .yml, or .json")
