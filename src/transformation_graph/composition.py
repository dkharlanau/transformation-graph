from __future__ import annotations

from pathlib import Path
from typing import Any

from .adapters import AdapterKind, graph_from_as_code
from .conformance import evaluate_adapter_graph, should_fail_conformance
from .model import Graph, GraphValidationError


def _merge_text(left: str | None, right: str | None) -> str | None:
    values = {value for value in (left, right) if value}
    if not values:
        return None
    return sorted(values, key=lambda value: (-len(value), value))[0]


def _merge_node(existing: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    if existing["type"] != candidate["type"]:
        raise GraphValidationError(
            f"cannot reconcile node '{existing['id']}': types differ ({existing['type']} vs {candidate['type']})"
        )
    result = dict(existing)
    titles = sorted({existing["title"], candidate["title"]})
    result["title"] = _merge_text(existing["title"], candidate["title"])
    if len(titles) > 1:
        attrs = dict(result.get("attributes", {}))
        attrs["x-title-aliases"] = titles
        result["attributes"] = attrs
    description = _merge_text(existing.get("description"), candidate.get("description"))
    if description:
        result["description"] = description
    tags = sorted(set(existing.get("tags", [])) | set(candidate.get("tags", [])))
    if tags:
        result["tags"] = tags

    attributes = dict(result.get("attributes", {}))
    for key, value in candidate.get("attributes", {}).items():
        if key not in attributes:
            attributes[key] = value
        elif attributes[key] != value:
            raise GraphValidationError(
                f"cannot reconcile node '{existing['id']}': attribute '{key}' conflicts"
            )
    if attributes:
        result["attributes"] = attributes
    return result


def compose_reconciled(
    graphs: list[Graph],
    project_id: str,
    project_name: str,
    description: str | None = None,
) -> Graph:
    """Compose complementary graph slices, reconciling same-ID nodes when metadata is compatible."""
    if not graphs:
        raise GraphValidationError("at least one graph is required for composition")
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str, str | None], dict[str, Any]] = {}
    source_records: list[dict[str, Any]] = []

    ordered_graphs = sorted(
        graphs,
        key=lambda graph: (
            str(graph.project.get("source_format") or ""),
            str(graph.project.get("source_file") or ""),
            str(graph.project.get("id") or ""),
        ),
    )
    for graph in ordered_graphs:
        source_records.append(
            {
                key: graph.project.get(key)
                for key in ("id", "source_format", "source_file")
                if graph.project.get(key) is not None
            }
        )
        for node in graph.nodes.values():
            candidate = node.as_dict()
            if node.id in nodes:
                nodes[node.id] = _merge_node(nodes[node.id], candidate)
            else:
                nodes[node.id] = candidate
        for edge in graph.edges:
            key = (edge.source, edge.target, edge.type, edge.label)
            edges.setdefault(key, edge.as_dict())

    project: dict[str, Any] = {
        "id": project_id,
        "name": project_name,
        "sources": source_records,
        "composition": "reconciled",
    }
    if description:
        project["description"] = description
    return Graph(
        {
            "version": "0.1",
            "project": project,
            "nodes": [nodes[node_id] for node_id in sorted(nodes)],
            "edges": [edges[key] for key in sorted(edges)],
        }
    )


def compose_adapter_documents(
    specs: list[tuple[AdapterKind, str | Path]],
    project_id: str,
    project_name: str,
    description: str | None = None,
    *,
    fail_on: str = "error",
) -> tuple[Graph, list[dict[str, Any]]]:
    """Normalize, conformance-check, and safely compose multiple as-code documents."""
    if not specs:
        raise GraphValidationError("at least one adapter document is required")
    graphs: list[Graph] = []
    checks: list[dict[str, Any]] = []
    for kind, path in sorted(specs, key=lambda item: (item[0], str(item[1]))):
        graph = graph_from_as_code(path, kind)
        check = evaluate_adapter_graph(graph, kind)
        checks.append(check)
        if should_fail_conformance(check, fail_on):
            raise GraphValidationError(
                f"{kind} adapter conformance failed for {path}: "
                f"{check['summary']['errors']} errors, {check['summary']['warnings']} warnings"
            )
        graphs.append(graph)
    return compose_reconciled(graphs, project_id, project_name, description), checks
