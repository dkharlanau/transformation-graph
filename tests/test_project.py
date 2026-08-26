from pathlib import Path

from transformation_graph import Graph
from transformation_graph.project import build_project, load_project_manifest

MANIFEST = Path("examples/project/transformation-project.yaml")


def test_project_manifest_builds_multi_domain_governed_graph_and_site(tmp_path: Path):
    report = build_project(MANIFEST, tmp_path / "build")
    build = tmp_path / "build"

    assert report["passed"] is True
    assert report["version"] == "0.2"
    assert report["governance"]["scorecard"]["score"] >= 85
    assert len(report["conformance"]) == 3
    assert report["links"]["count"] >= 10
    assert len(report["sources"]["graphs"]) == 4
    assert (build / "graph.yaml").exists()
    assert (build / "build-report.json").exists()
    assert (build / "site" / "index.html").exists()
    assert (build / "site" / "scorecard.json").exists()
    assert (build / "site" / "graph.graphml").exists()

    graph = Graph.from_file(build / "graph.yaml")
    for node_id in [
        "mapping.customer-core",
        "interface.CUSTOMER-MDG-S4-01",
        "process.customer_creation",
        "test.customer-reconciliation",
        "change.customer-cutover",
        "evidence.mapping-approval",
        "process.cutover-execution",
    ]:
        assert node_id in graph.nodes
    assert graph.project["cross_source_links"] == report["links"]["count"]
    assert graph.path("change.customer-cutover", "evidence.mapping-approval", undirected=True) is not None
    assert graph.path("process.cutover-execution", "interface.CUSTOMER-MDG-S4-01", undirected=True) is not None


def test_project_manifest_resolves_relative_sources_and_links():
    source, manifest = load_project_manifest(MANIFEST)
    assert source == MANIFEST
    assert manifest["project"]["id"] == "customer-domain-reference"
    assert len(manifest["sources"]["graphs"]) == 4
    assert len(manifest["links"]) >= 10
