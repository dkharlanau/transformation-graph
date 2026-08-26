from pathlib import Path

from transformation_graph import Graph
from transformation_graph.governance_views import build_governance_view, render_governance_view
from transformation_graph.site_export import build_site
from transformation_graph.site_extensions import augment_site

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_ownership_and_test_views_expose_coverage_and_gaps():
    graph = Graph.from_file(EXAMPLE)
    ownership = build_governance_view(graph, "ownership")
    tests = build_governance_view(graph, "test-coverage")
    assert ownership["summary"]["total"] > 0
    assert tests["summary"]["total"] > 0
    assert "Ownership traceability" in render_governance_view(ownership, "html")
    assert "test-coverage" in render_governance_view(tests, "json")


def test_change_readiness_is_dimension_explicit():
    report = build_governance_view(Graph.from_file(EXAMPLE), "change-readiness")
    assert report["summary"]["changes"] == 1
    row = report["rows"][0]
    assert row["total_dimensions"] == 6
    assert {item["id"] for item in row["dimensions"]} == {"owner", "test", "system", "interface", "mapping", "evidence"}


def test_site_augmentation_adds_graphml_and_governance_views(tmp_path):
    graph = Graph.from_file(EXAMPLE)
    site = tmp_path / "site"
    manifest = augment_site(graph, site, build_site(graph, site))
    assert manifest["version"] == "0.3"
    assert (site / "graph.graphml").exists()
    assert (site / "governance.html").exists()
    assert (site / "views" / "ownership.json").exists()
    assert "graph.graphml" in (site / "llms.txt").read_text(encoding="utf-8")
    assert "governance.html" in (site / "index.html").read_text(encoding="utf-8")
