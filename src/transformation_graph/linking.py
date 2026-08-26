from __future__ import annotations

from typing import Any

from .model import Graph, GraphValidationError


def validate_links(raw_links: object, location: str = "links") -> list[dict[str, Any]]:
    """Validate cross-source relationship declarations without resolving endpoints yet."""
    if raw_links is None:
        return []
    if not isinstance(raw_links, list):
        raise GraphValidationError(f"{location} must be a list")
    links: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str | None]] = set()
    for index, item in enumerate(raw_links):
        prefix = f"{location}[{index}]"
        if not isinstance(item, dict):
            raise GraphValidationError(f"{prefix} must be an object")
        source = item.get("from")
        target = item.get("to")
        relation = item.get("type")
        label = item.get("label")
        attributes = item.get("attributes", {})
        if not isinstance(source, str) or not source:
            raise GraphValidationError(f"{prefix}.from must be a non-empty string")
        if not isinstance(target, str) or not target:
            raise GraphValidationError(f"{prefix}.to must be a non-empty string")
        if not isinstance(relation, str) or not relation:
            raise GraphValidationError(f"{prefix}.type must be a non-empty string")
        if label is not None and not isinstance(label, str):
            raise GraphValidationError(f"{prefix}.label must be a string")
        if not isinstance(attributes, dict):
            raise GraphValidationError(f"{prefix}.attributes must be an object")
        key = (source, target, relation, label)
        if key in seen:
            raise GraphValidationError(f"duplicate cross-source link: {source} -[{relation}]-> {target}")
        seen.add(key)
        link: dict[str, Any] = {"from": source, "to": target, "type": relation}
        if label:
            link["label"] = label
        if attributes:
            link["attributes"] = attributes
        links.append(link)
    return links


def apply_links(graph: Graph, raw_links: object) -> Graph:
    """Add validated cross-source links after all source graphs have been composed."""
    links = validate_links(raw_links)
    if not links:
        return graph
    existing = {
        (edge.source, edge.target, edge.type, edge.label): edge.as_dict()
        for edge in graph.edges
    }
    additions: list[dict[str, Any]] = []
    for link in links:
        source, target = link["from"], link["to"]
        if source not in graph.nodes:
            raise GraphValidationError(f"cross-source link references unknown source node '{source}'")
        if target not in graph.nodes:
            raise GraphValidationError(f"cross-source link references unknown target node '{target}'")
        key = (source, target, link["type"], link.get("label"))
        if key in existing:
            if existing[key] != link:
                raise GraphValidationError(
                    f"cross-source link conflicts with existing edge: {source} -[{link['type']}]-> {target}"
                )
            continue
        existing[key] = link
        additions.append(link)
    raw = graph.as_dict()
    raw["project"] = dict(raw["project"])
    raw["project"]["cross_source_links"] = len(links)
    raw["edges"] = raw["edges"] + additions
    return Graph(raw)
