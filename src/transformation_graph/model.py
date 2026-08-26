from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import yaml


CANONICAL_NODE_TYPES = {
    "process",
    "process_step",
    "system",
    "business_object",
    "data_object",
    "field",
    "interface",
    "mapping",
    "rule",
    "requirement",
    "test",
    "change",
    "owner",
    "decision",
    "evidence",
}


class GraphValidationError(ValueError):
    """Raised when a transformation graph violates deterministic model rules."""


@dataclass(frozen=True)
class Node:
    id: str
    type: str
    title: str
    description: str | None
    tags: tuple[str, ...]
    attributes: dict[str, Any]


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: str
    label: str | None
    attributes: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"from": self.source, "to": self.target, "type": self.type}
        if self.label:
            data["label"] = self.label
        if self.attributes:
            data["attributes"] = self.attributes
        return data


class Graph:
    def __init__(self, raw: dict[str, Any]):
        self.raw = raw
        self.version = str(raw.get("version", ""))
        self.project = raw.get("project", {})
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._validate_and_build()

    @classmethod
    def from_file(cls, path: str | Path) -> "Graph":
        path = Path(path)
        with path.open("r", encoding="utf-8") as handle:
            if path.suffix.lower() in {".yaml", ".yml"}:
                raw = yaml.safe_load(handle)
            elif path.suffix.lower() == ".json":
                raw = json.load(handle)
            else:
                raise GraphValidationError("Graph file must be YAML (.yaml/.yml) or JSON (.json).")
        if not isinstance(raw, dict):
            raise GraphValidationError("Top-level graph document must be an object.")
        return cls(raw)

    def _validate_and_build(self) -> None:
        errors: list[str] = []

        if self.version != "0.1":
            errors.append("version must be '0.1'")

        if not isinstance(self.project, dict):
            errors.append("project must be an object")
        else:
            if not self.project.get("id"):
                errors.append("project.id is required")
            if not self.project.get("name"):
                errors.append("project.name is required")

        raw_nodes = self.raw.get("nodes")
        if not isinstance(raw_nodes, list) or not raw_nodes:
            errors.append("nodes must be a non-empty list")
            raw_nodes = []

        for index, item in enumerate(raw_nodes):
            prefix = f"nodes[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue

            node_id = item.get("id")
            node_type = item.get("type")
            title = item.get("title")
            if not isinstance(node_id, str) or not node_id.strip():
                errors.append(f"{prefix}.id must be a non-empty string")
                continue
            if node_id in self.nodes:
                errors.append(f"duplicate node id: {node_id}")
                continue
            if not isinstance(node_type, str) or not node_type.strip():
                errors.append(f"{prefix}.type must be a non-empty string")
                continue
            if node_type not in CANONICAL_NODE_TYPES and not node_type.startswith("x-"):
                errors.append(
                    f"{prefix}.type '{node_type}' is not canonical; custom types must start with 'x-'"
                )
            if not isinstance(title, str) or not title.strip():
                errors.append(f"{prefix}.title must be a non-empty string")
                continue

            tags = item.get("tags", [])
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
                errors.append(f"{prefix}.tags must be a list of strings")
                tags = []

            attributes = item.get("attributes", {})
            if not isinstance(attributes, dict):
                errors.append(f"{prefix}.attributes must be an object")
                attributes = {}

            description = item.get("description")
            if description is not None and not isinstance(description, str):
                errors.append(f"{prefix}.description must be a string")
                description = None

            self.nodes[node_id] = Node(
                id=node_id,
                type=node_type,
                title=title,
                description=description,
                tags=tuple(tags),
                attributes=attributes,
            )

        raw_edges = self.raw.get("edges", [])
        if not isinstance(raw_edges, list):
            errors.append("edges must be a list")
            raw_edges = []

        seen_edges: set[tuple[str, str, str, str | None]] = set()
        for index, item in enumerate(raw_edges):
            prefix = f"edges[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue

            source = item.get("from")
            target = item.get("to")
            edge_type = item.get("type")
            label = item.get("label")
            attributes = item.get("attributes", {})

            if not isinstance(source, str) or not source:
                errors.append(f"{prefix}.from must be a non-empty string")
                continue
            if not isinstance(target, str) or not target:
                errors.append(f"{prefix}.to must be a non-empty string")
                continue
            if not isinstance(edge_type, str) or not edge_type:
                errors.append(f"{prefix}.type must be a non-empty string")
                continue
            if label is not None and not isinstance(label, str):
                errors.append(f"{prefix}.label must be a string")
                label = None
            if not isinstance(attributes, dict):
                errors.append(f"{prefix}.attributes must be an object")
                attributes = {}

            if source not in self.nodes:
                errors.append(f"{prefix}.from references unknown node '{source}'")
            if target not in self.nodes:
                errors.append(f"{prefix}.to references unknown node '{target}'")

            key = (source, target, edge_type, label)
            if key in seen_edges:
                errors.append(
                    f"duplicate edge: {source} -[{edge_type}]-> {target}"
                    + (f" ({label})" if label else "")
                )
            seen_edges.add(key)
            self.edges.append(
                Edge(source=source, target=target, type=edge_type, label=label, attributes=attributes)
            )

        if errors:
            raise GraphValidationError("\n".join(errors))

    def stats(self) -> dict[str, Any]:
        return {
            "project": self.project.get("id"),
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "node_types": dict(sorted(Counter(node.type for node in self.nodes.values()).items())),
            "edge_types": dict(sorted(Counter(edge.type for edge in self.edges).items())),
        }

    def path(self, source: str, target: str, undirected: bool = False) -> list[str] | None:
        if source not in self.nodes:
            raise GraphValidationError(f"unknown source node: {source}")
        if target not in self.nodes:
            raise GraphValidationError(f"unknown target node: {target}")
        if source == target:
            return [source]

        adjacency: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            adjacency[edge.source].append(edge.target)
            if undirected:
                adjacency[edge.target].append(edge.source)

        queue: deque[str] = deque([source])
        parent: dict[str, str | None] = {source: None}

        while queue:
            current = queue.popleft()
            for neighbor in sorted(adjacency[current]):
                if neighbor in parent:
                    continue
                parent[neighbor] = current
                if neighbor == target:
                    result = [target]
                    while parent[result[-1]] is not None:
                        result.append(parent[result[-1]])  # type: ignore[arg-type]
                    return list(reversed(result))
                queue.append(neighbor)
        return None

    def context(self, node_id: str, depth: int = 1) -> dict[str, Any]:
        if node_id not in self.nodes:
            raise GraphValidationError(f"unknown node: {node_id}")
        if depth < 0:
            raise GraphValidationError("depth must be >= 0")

        selected = {node_id}
        frontier = {node_id}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for edge in self.edges:
                if edge.source in frontier:
                    next_frontier.add(edge.target)
                if edge.target in frontier:
                    next_frontier.add(edge.source)
            next_frontier -= selected
            selected |= next_frontier
            frontier = next_frontier

        nodes = [
            {
                "id": node.id,
                "type": node.type,
                "title": node.title,
                **({"description": node.description} if node.description else {}),
                **({"tags": list(node.tags)} if node.tags else {}),
                **({"attributes": node.attributes} if node.attributes else {}),
            }
            for node in sorted(
                (self.nodes[item] for item in selected),
                key=lambda item: (item.type, item.id),
            )
        ]
        edges = [
            edge.as_dict()
            for edge in self.edges
            if edge.source in selected and edge.target in selected
        ]
        return {"root": node_id, "depth": depth, "nodes": nodes, "edges": edges}

    def impact(
        self,
        node_id: str,
        depth: int = 2,
        direction: str = "both",
        relations: set[str] | None = None,
    ) -> dict[str, Any]:
        if node_id not in self.nodes:
            raise GraphValidationError(f"unknown node: {node_id}")
        if depth < 0:
            raise GraphValidationError("depth must be >= 0")
        if direction not in {"in", "out", "both"}:
            raise GraphValidationError("direction must be one of: in, out, both")

        selected = {node_id}
        frontier = {node_id}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for edge in self.edges:
                if relations and edge.type not in relations:
                    continue
                if direction in {"out", "both"} and edge.source in frontier:
                    next_frontier.add(edge.target)
                if direction in {"in", "both"} and edge.target in frontier:
                    next_frontier.add(edge.source)
            next_frontier -= selected
            if not next_frontier:
                break
            selected |= next_frontier
            frontier = next_frontier

        impacted = [
            {"id": self.nodes[item].id, "type": self.nodes[item].type, "title": self.nodes[item].title}
            for item in sorted(selected)
            if item != node_id
        ]
        traversed_edges = [
            edge.as_dict()
            for edge in self.edges
            if edge.source in selected and edge.target in selected and (not relations or edge.type in relations)
        ]
        return {"root": node_id, "depth": depth, "direction": direction, "relations": sorted(relations) if relations else [], "impacted_nodes": impacted, "edges": traversed_edges}

    def quality(self) -> dict[str, Any]:
        findings: list[dict[str, str]] = []
        incident: Counter[str] = Counter()
        outgoing: dict[str, list[Edge]] = {node_id: [] for node_id in self.nodes}
        incoming: dict[str, list[Edge]] = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            incident[edge.source] += 1
            incident[edge.target] += 1
            outgoing[edge.source].append(edge)
            incoming[edge.target].append(edge)

        for node in sorted(self.nodes.values(), key=lambda item: item.id):
            if incident[node.id] == 0:
                findings.append({"code": "ORPHAN_NODE", "severity": "error", "node": node.id, "message": f"{node.type} '{node.title}' has no relationships"})
            if node.type == "mapping" and not any(edge.type == "evidenced_by" for edge in outgoing[node.id]):
                findings.append({"code": "MAPPING_WITHOUT_EVIDENCE", "severity": "warning", "node": node.id, "message": "mapping has no evidenced_by relationship"})
            if node.type == "decision" and not any(edge.type == "owned_by" and self.nodes[edge.target].type == "owner" for edge in outgoing[node.id]):
                findings.append({"code": "DECISION_WITHOUT_OWNER", "severity": "warning", "node": node.id, "message": "decision has no owner"})
            if node.type == "change" and not any(edge.type in {"covered_by", "validated_by"} and self.nodes[edge.target].type == "test" for edge in outgoing[node.id]):
                findings.append({"code": "CHANGE_WITHOUT_TEST", "severity": "warning", "node": node.id, "message": "change has no direct test coverage relationship"})
            if node.type == "test" and not any(edge.type in {"validates", "covers"} for edge in outgoing[node.id]):
                findings.append({"code": "TEST_WITHOUT_TARGET", "severity": "warning", "node": node.id, "message": "test does not validate or cover another node"})

        errors = sum(item["severity"] == "error" for item in findings)
        warnings = sum(item["severity"] == "warning" for item in findings)
        return {"passed": errors == 0 and warnings == 0, "summary": {"errors": errors, "warnings": warnings, "findings": len(findings)}, "findings": findings}

    def mermaid(self, focus: str | None = None, depth: int = 1) -> str:
        if focus is None:
            selected = set(self.nodes)
        else:
            context = self.context(focus, depth=depth)
            selected = {item["id"] for item in context["nodes"]}
        ordered = sorted(selected)
        aliases = {node_id: f"n{index}" for index, node_id in enumerate(ordered)}

        def escape(value: str) -> str:
            return value.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

        lines = ["graph LR"]
        for node_id in ordered:
            node = self.nodes[node_id]
            label = escape(f"{node.title} ({node.type})")
            lines.append(f'  {aliases[node_id]}["{label}"]')
        for edge in self.edges:
            if edge.source not in selected or edge.target not in selected:
                continue
            label = escape(edge.label or edge.type)
            lines.append(f"  {aliases[edge.source]} -->|{label}| {aliases[edge.target]}")
        return "\n".join(lines) + "\n"
