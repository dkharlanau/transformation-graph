from pathlib import Path

from transformation_graph import Graph
from transformation_graph.site_export import build_site

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_site_bundle_contains_human_and_machine_artifacts(tmp_path: Path):
    graph = Graph.from_file(EXAMPLE)
    manifest = build_site(
        graph,
        tmp_path / "site",
        base_url="https://example.test/transformation-graph/",
    )
    site = tmp_path / "site"

    for path in [
        "index.html",
        "explorer.html",
        "graph.json",
        "catalog.json",
        "manifest.json",
        "llms.txt",
        "robots.txt",
        "sitemap.xml",
        ".nojekyll",
        "roles/architect.json",
        "roles/integration.csv",
        "roles/data.md",
        "roles/test.html",
        "roles/cutover.json",
    ]:
        assert (site / path).exists(), path

    assert manifest["format"] == "transformation-graph-site"
    assert "mapping.customer-to-bp" in (site / "graph.json").read_text(encoding="utf-8")
    assert "Role-oriented deterministic traceability" in (site / "llms.txt").read_text(encoding="utf-8")
    assert 'rel="canonical"' in (site / "index.html").read_text(encoding="utf-8")
    assert "<svg" in (site / "explorer.html").read_text(encoding="utf-8")
