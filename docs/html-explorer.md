# HTML/SVG explorer

The `html` command generates one self-contained file with no external JavaScript, CSS, fonts, or network calls.

```bash
transformation-graph html graph.yaml --output graph.html
```

The explorer contains two synchronized ways to navigate the model:

1. a searchable/type-filterable node inventory with attributes and direct relationships;
2. an interactive SVG dependency canvas generated directly from the graph data.

Nodes are grouped into deterministic type columns. Selecting a node from either view highlights it and its direct neighbors while dimming unrelated nodes and edges. Clicking a relation in the detail view jumps to the connected node. Search and type filtering also reduce the visible SVG graph.

The canvas intentionally uses a simple deterministic layout rather than a force simulation. This keeps exported views reproducible, dependency-free, and suitable for static hosting and offline project packages.

The output can be opened locally, attached to a project deliverable, or published as a static artifact. A dedicated GitHub Pages workflow remains on the roadmap.
