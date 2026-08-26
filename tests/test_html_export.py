from pathlib import Path

from transformation_graph import Graph
from transformation_graph.html_export import render_html, write_html

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_html_export_is_single_file_and_contains_graph_data():
    html = render_html(Graph.from_file(EXAMPLE))
    assert html.startswith("<!doctype html>")
    assert "Customer Master Migration to SAP S/4HANA" in html
    assert "const GRAPH_DATA =" in html
    assert "mapping.customer-to-bp" in html
    assert "https://" not in html


def test_html_export_writes_file(tmp_path):
    output = tmp_path / "explorer.html"
    write_html(Graph.from_file(EXAMPLE), output, title="Migration Explorer")
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "Migration Explorer" in text
    assert "Search nodes" in text
