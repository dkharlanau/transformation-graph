from pathlib import Path

from transformation_graph import Graph
from transformation_graph.traceability import (
    ROLE_PRESETS,
    render_traceability_csv,
    render_traceability_markdown,
    role_traceability,
    traceability_matrix,
)

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_traceability_matrix_finds_mapping_fields_with_relations():
    graph = Graph.from_file(EXAMPLE)
    report = traceability_matrix(graph, {"mapping"}, {"field"}, max_depth=2)

    target_ids = {row["target"]["id"] for row in report["rows"]}
    assert {"field.kunnr", "field.bp-id"}.issubset(target_ids)
    kunnr = next(row for row in report["rows"] if row["target"]["id"] == "field.kunnr")
    assert kunnr["hops"] == 1
    assert kunnr["relations"][0]["type"] == "reads"
    assert "mapping.customer-to-bp" in kunnr["path_text"]


def test_role_traceability_exposes_architect_coverage():
    graph = Graph.from_file(EXAMPLE)
    report = role_traceability(graph, "architect", max_depth=4)

    assert report["role"] == "architect"
    assert report["summary"]["paths"] > 0
    assert any(
        row["source"]["type"] == "process" and row["target"]["type"] == "system"
        for row in report["rows"]
    )
    assert len(report["coverage"]) == len(ROLE_PRESETS["architect"]["pairs"])


def test_traceability_reports_render_markdown_and_csv():
    graph = Graph.from_file(EXAMPLE)
    report = role_traceability(graph, "integration", max_depth=4)

    markdown = render_traceability_markdown(report)
    csv_text = render_traceability_csv(report)

    assert "# Integration traceability" in markdown
    assert "## Coverage" in markdown
    assert csv_text.startswith("source_id,source_type,source_title,target_id")
    assert "interface.customer-load" in csv_text
