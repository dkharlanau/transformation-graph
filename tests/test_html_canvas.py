from pathlib import Path

from transformation_graph import Graph
from transformation_graph.html_export import render_html

EXAMPLE = Path("examples/sap-s4-customer-migration.yaml")


def test_html_explorer_contains_interactive_svg_canvas():
    html = render_html(Graph.from_file(EXAMPLE))
    assert 'id="graphView"' in html
    assert "function renderGraph(nodes)" in html
    assert "graph-edge" in html
    assert "graph-node" in html
    assert "https://" not in html
