from pathlib import Path

from transformation_graph import Graph
from transformation_graph.project import build_project, load_project_manifest

MANIFEST = Path("examples/project/transformation-project.yaml")


def test_project_manifest_builds_governed_graph_and_site(tmp_path: Path):
    report = build_project(MANIFEST, tmp_path / "build")
    build = tmp_path / "build"

    assert report["passed"] is True
    scorecard = report["governance"]["scorecard"]
    assert scorecard["score"] >= 60
    assert scorecard["summary"]["gaps"] > 0
    assert len(report["conformance"]) == 3
    assert (build / "graph.yaml").exists()
    assert (build / "build-report.json").exists()
    assert (build / "site" / "index.html").exists()
    assert (build / "site" / "scorecard.json").exists()

    graph = Graph.from_file(build / "graph.yaml")
    assert "mapping.customer-core" in graph.nodes
    assert "interface.CUSTOMER-MDG-S4-01" in graph.nodes
    assert "process.customer_creation" in graph.nodes


def test_project_manifest_resolves_relative_sources():
    source, manifest = load_project_manifest(MANIFEST)
    assert source == MANIFEST
    assert manifest["project"]["id"] == "customer-domain-reference"
