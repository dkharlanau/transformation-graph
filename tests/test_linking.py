import pytest

from transformation_graph.linking import apply_links, validate_links
from transformation_graph.model import Graph, GraphValidationError


def _graph() -> Graph:
    return Graph({
        "version": "0.1",
        "project": {"id": "demo", "name": "Demo"},
        "nodes": [
            {"id": "system.a", "type": "system", "title": "A"},
            {"id": "system.b", "type": "system", "title": "B"},
        ],
        "edges": [],
    })


def test_apply_links_connects_independent_source_nodes():
    graph = apply_links(_graph(), [{"from": "system.a", "to": "system.b", "type": "same_as"}])
    assert graph.stats()["edges"] == 1
    assert graph.project["cross_source_links"] == 1
    assert graph.path("system.a", "system.b") == ["system.a", "system.b"]


def test_apply_links_fails_on_unknown_endpoint():
    with pytest.raises(GraphValidationError, match="unknown target node"):
        apply_links(_graph(), [{"from": "system.a", "to": "system.missing", "type": "same_as"}])


def test_validate_links_rejects_duplicate_identity():
    with pytest.raises(GraphValidationError, match="duplicate cross-source link"):
        validate_links([
            {"from": "system.a", "to": "system.b", "type": "same_as"},
            {"from": "system.a", "to": "system.b", "type": "same_as"},
        ])
