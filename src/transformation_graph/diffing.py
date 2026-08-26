from __future__ import annotations

from typing import Any

from .model import Edge, Graph


def _edge_key(edge: Edge) -> tuple[str, str, str, str | None]:
    return (edge.source, edge.target, edge.type, edge.label)


def graph_diff(before: Graph, after: Graph) -> dict[str, Any]:
    """Compare two graph snapshots using stable node IDs and edge identities."""
    before_nodes = {node_id: node.as_dict() for node_id, node in before.nodes.items()}
    after_nodes = {node_id: node.as_dict() for node_id, node in after.nodes.items()}

    added_node_ids = sorted(set(after_nodes) - set(before_nodes))
    removed_node_ids = sorted(set(before_nodes) - set(after_nodes))
    common_node_ids = sorted(set(before_nodes) & set(after_nodes))

    nodes_added = [after_nodes[node_id] for node_id in added_node_ids]
    nodes_removed = [before_nodes[node_id] for node_id in removed_node_ids]
    nodes_changed = [
        {"id": node_id, "before": before_nodes[node_id], "after": after_nodes[node_id]}
        for node_id in common_node_ids
        if before_nodes[node_id] != after_nodes[node_id]
    ]

    before_edges = {_edge_key(edge): edge.as_dict() for edge in before.edges}
    after_edges = {_edge_key(edge): edge.as_dict() for edge in after.edges}
    added_edge_keys = sorted(set(after_edges) - set(before_edges))
    removed_edge_keys = sorted(set(before_edges) - set(after_edges))
    common_edge_keys = sorted(set(before_edges) & set(after_edges))

    edges_added = [after_edges[key] for key in added_edge_keys]
    edges_removed = [before_edges[key] for key in removed_edge_keys]
    edges_changed = [
        {"identity": list(key), "before": before_edges[key], "after": after_edges[key]}
        for key in common_edge_keys
        if before_edges[key] != after_edges[key]
    ]

    changed_roots = set(added_node_ids) | set(removed_node_ids)
    changed_roots.update(item["id"] for item in nodes_changed)
    for edge in edges_added + edges_removed:
        changed_roots.add(edge["from"])
        changed_roots.add(edge["to"])
    for item in edges_changed:
        changed_roots.add(item["before"]["from"])
        changed_roots.add(item["before"]["to"])

    return {
        "before_project": before.project.get("id"),
        "after_project": after.project.get("id"),
        "summary": {
            "nodes_added": len(nodes_added),
            "nodes_removed": len(nodes_removed),
            "nodes_changed": len(nodes_changed),
            "edges_added": len(edges_added),
            "edges_removed": len(edges_removed),
            "edges_changed": len(edges_changed),
        },
        "changed_roots": sorted(changed_roots),
        "nodes": {"added": nodes_added, "removed": nodes_removed, "changed": nodes_changed},
        "edges": {"added": edges_added, "removed": edges_removed, "changed": edges_changed},
    }


def diff_with_impact(before: Graph, after: Graph, depth: int = 1) -> dict[str, Any]:
    """Add neighboring impact around every changed root to a graph diff."""
    report = graph_diff(before, after)
    roots = set(report["changed_roots"])
    impacted: dict[str, dict[str, str]] = {}

    for root in sorted(roots):
        graph = after if root in after.nodes else before
        if root not in graph.nodes:
            continue
        traversal = graph.impact(root, depth=depth, direction="both")
        for node in traversal["impacted_nodes"]:
            if node["id"] not in roots:
                impacted[node["id"]] = node

    report["impact"] = {
        "depth": depth,
        "impacted_nodes": [impacted[node_id] for node_id in sorted(impacted)],
    }
    return report
