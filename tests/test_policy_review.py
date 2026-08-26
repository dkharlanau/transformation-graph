from pathlib import Path

import yaml

from transformation_graph import Graph
from transformation_graph.policy import evaluate_policy_files, evaluate_policy_pack, load_policy_pack, should_fail
from transformation_graph.review import build_review_report, render_markdown_report, write_review_report

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")
BEFORE = Path("examples/change/before.yaml")
AFTER = Path("examples/change/after.yaml")
BASELINE = Path("policies/enterprise-baseline.yaml")


def test_enterprise_baseline_passes_canonical_example():
    report = evaluate_policy_files(Graph.from_file(EXAMPLE), [BASELINE])
    assert report["summary"] == {"errors": 0, "warnings": 0, "info": 0, "findings": 0}
    assert not should_fail(report, "error")


def test_require_relation_policy_finds_missing_mapping_evidence(tmp_path: Path):
    graph = Graph({"version": "0.1", "project": {"id": "policy-demo", "name": "Policy Demo"}, "nodes": [{"id": "mapping.customer", "type": "mapping", "title": "Customer mapping"}, {"id": "system.s4", "type": "system", "title": "SAP S/4HANA"}], "edges": [{"from": "mapping.customer", "to": "system.s4", "type": "targets"}]})
    policy_file = tmp_path / "policy.yaml"
    policy_file.write_text(yaml.safe_dump({"version": "0.1", "policy": {"id": "mapping-governance", "name": "Mapping governance", "rules": [{"id": "mapping-evidence", "kind": "require_relation", "node_type": "mapping", "direction": "out", "relations": ["evidenced_by"], "target_type": "evidence", "severity": "error"}]}}, sort_keys=False), encoding="utf-8")
    report = evaluate_policy_pack(graph, load_policy_pack(policy_file))
    assert report["summary"]["errors"] == 1
    assert report["findings"][0]["node"] == "mapping.customer"
    assert should_fail(report, "error")


def test_review_report_prioritizes_changed_enterprise_nodes(tmp_path: Path):
    report = build_review_report(Graph.from_file(BEFORE), Graph.from_file(AFTER), impact_depth=1)
    assert report["change_summary"]["nodes_added"] == 1
    assert report["change_summary"]["nodes_changed"] == 1
    assert report["attention_summary"]["high"] == 2
    assert {node["id"] for node in report["impact"]["nodes"]} == {"system.erp", "test.customer"}
    markdown = render_markdown_report(report)
    assert "# Transformation Graph change review" in markdown
    assert "`interface.customer`" in markdown
    assert "SAP S/4HANA" in markdown
    output = tmp_path / "review.md"
    write_review_report(report, output)
    assert output.read_text(encoding="utf-8") == markdown
