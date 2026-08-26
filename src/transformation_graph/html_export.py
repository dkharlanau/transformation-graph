from __future__ import annotations

from html import escape
from pathlib import Path
import json

from .model import Graph


def render_html(graph: Graph, title: str | None = None) -> str:
    """Render a dependency-free, single-file transformation graph explorer."""
    page_title = title or str(graph.project.get("name") or graph.project.get("id") or "Transformation Graph")
    payload = {
        "project": graph.project,
        "stats": graph.stats(),
        "nodes": [graph.nodes[node_id].as_dict() for node_id in sorted(graph.nodes)],
        "edges": sorted(
            (edge.as_dict() for edge in graph.edges),
            key=lambda item: (item["from"], item["to"], item["type"], item.get("label", "")),
        ),
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    safe_title = escape(page_title)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title} · Transformation Graph</title>
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: Canvas; color: CanvasText; }}
    header {{ padding: 28px 32px 18px; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }}
    h1 {{ margin: 0 0 6px; font-size: clamp(24px, 3vw, 38px); letter-spacing: -0.03em; }}
    .muted {{ opacity: .68; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 18px; max-width: 760px; }}
    .stat {{ padding: 12px 14px; border: 1px solid color-mix(in srgb, CanvasText 14%, transparent); border-radius: 12px; }}
    .stat strong {{ display: block; font-size: 22px; }}
    main {{ display: grid; grid-template-columns: minmax(260px, 360px) minmax(0, 1fr); min-height: calc(100vh - 170px); }}
    aside {{ border-right: 1px solid color-mix(in srgb, CanvasText 15%, transparent); padding: 18px; }}
    .controls {{ display: grid; gap: 10px; position: sticky; top: 0; background: Canvas; padding-bottom: 12px; }}
    input, select {{ width: 100%; padding: 10px 12px; border-radius: 9px; border: 1px solid color-mix(in srgb, CanvasText 22%, transparent); background: Canvas; color: CanvasText; }}
    #nodeList {{ display: grid; gap: 6px; margin-top: 8px; }}
    button.node {{ text-align: left; padding: 10px 11px; border-radius: 9px; border: 1px solid transparent; background: color-mix(in srgb, CanvasText 5%, transparent); color: CanvasText; cursor: pointer; }}
    button.node:hover, button.node.active {{ border-color: color-mix(in srgb, CanvasText 25%, transparent); background: color-mix(in srgb, CanvasText 9%, transparent); }}
    button.node small {{ display: block; opacity: .62; margin-top: 3px; }}
    section.detail {{ padding: 28px 32px; max-width: 1100px; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: .08em; font-size: 12px; opacity: .6; }}
    h2 {{ font-size: clamp(24px, 3vw, 34px); margin: 6px 0 10px; letter-spacing: -0.025em; }}
    .panel {{ border: 1px solid color-mix(in srgb, CanvasText 14%, transparent); border-radius: 14px; padding: 16px; margin: 18px 0; }}
    dl {{ display: grid; grid-template-columns: 140px minmax(0, 1fr); gap: 8px 14px; margin: 0; }}
    dt {{ opacity: .62; }} dd {{ margin: 0; overflow-wrap: anywhere; }}
    .relations {{ display: grid; gap: 8px; }}
    .relation {{ padding: 10px 12px; border-radius: 10px; background: color-mix(in srgb, CanvasText 5%, transparent); }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: .92em; }}
    @media (max-width: 760px) {{ .stats {{ grid-template-columns: repeat(2, 1fr); }} main {{ grid-template-columns: 1fr; }} aside {{ border-right: 0; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }} section.detail {{ padding: 22px 18px; }} }}
  </style>
</head>
<body>
<header>
  <div class="eyebrow">Transformation Graph</div>
  <h1>{safe_title}</h1>
  <div class="muted" id="projectDescription"></div>
  <div class="stats">
    <div class="stat"><strong id="nodeCount">0</strong><span class="muted">nodes</span></div>
    <div class="stat"><strong id="edgeCount">0</strong><span class="muted">relations</span></div>
    <div class="stat"><strong id="typeCount">0</strong><span class="muted">node types</span></div>
    <div class="stat"><strong id="relationCount">0</strong><span class="muted">relation types</span></div>
  </div>
</header>
<main>
  <aside>
    <div class="controls">
      <input id="search" type="search" placeholder="Search nodes…" aria-label="Search nodes">
      <select id="typeFilter" aria-label="Filter by node type"><option value="">All node types</option></select>
      <div class="muted" id="visibleCount"></div>
    </div>
    <div id="nodeList"></div>
  </aside>
  <section class="detail" id="detail">
    <div class="eyebrow">Select a node</div>
    <h2>Explore transformation dependencies</h2>
    <p class="muted">Search or filter the inventory, then select a node to inspect its attributes and direct incoming/outgoing relationships.</p>
  </section>
</main>
<script>
const GRAPH_DATA = {data};
const byId = new Map(GRAPH_DATA.nodes.map(node => [node.id, node]));
const search = document.getElementById('search');
const typeFilter = document.getElementById('typeFilter');
const nodeList = document.getElementById('nodeList');
const detail = document.getElementById('detail');
let selectedId = null;

document.getElementById('projectDescription').textContent = GRAPH_DATA.project.description || GRAPH_DATA.project.id || '';
document.getElementById('nodeCount').textContent = GRAPH_DATA.nodes.length;
document.getElementById('edgeCount').textContent = GRAPH_DATA.edges.length;
document.getElementById('typeCount').textContent = Object.keys(GRAPH_DATA.stats.node_types || {{}}).length;
document.getElementById('relationCount').textContent = Object.keys(GRAPH_DATA.stats.edge_types || {{}}).length;

for (const type of [...new Set(GRAPH_DATA.nodes.map(node => node.type))].sort()) {{
  const option = document.createElement('option'); option.value = type; option.textContent = type; typeFilter.appendChild(option);
}}

function text(element, value) {{ element.textContent = value == null ? '' : String(value); return element; }}
function el(name, className) {{ const element = document.createElement(name); if (className) element.className = className; return element; }}

function renderList() {{
  const query = search.value.trim().toLowerCase();
  const type = typeFilter.value;
  const nodes = GRAPH_DATA.nodes.filter(node => (!type || node.type === type) && (!query || `${{node.id}} ${{node.title}} ${{node.type}} ${{node.description || ''}}`.toLowerCase().includes(query)));
  nodeList.replaceChildren();
  document.getElementById('visibleCount').textContent = `${{nodes.length}} of ${{GRAPH_DATA.nodes.length}} nodes`;
  for (const node of nodes) {{
    const button = el('button', 'node' + (node.id === selectedId ? ' active' : ''));
    button.type = 'button'; button.addEventListener('click', () => selectNode(node.id));
    text(button.appendChild(el('div')), node.title);
    text(button.appendChild(el('small')), `${{node.type}} · ${{node.id}}`);
    nodeList.appendChild(button);
  }}
}}

function addPair(dl, key, value) {{
  text(dl.appendChild(el('dt')), key);
  const dd = dl.appendChild(el('dd'));
  if (typeof value === 'object' && value !== null) text(dd.appendChild(el('code')), JSON.stringify(value)); else text(dd, value);
}}

function selectNode(id) {{
  selectedId = id; const node = byId.get(id); renderList(); detail.replaceChildren();
  text(detail.appendChild(el('div', 'eyebrow')), node.type);
  text(detail.appendChild(el('h2')), node.title);
  if (node.description) text(detail.appendChild(el('p', 'muted')), node.description);
  const panel = detail.appendChild(el('div', 'panel')); const dl = panel.appendChild(el('dl'));
  addPair(dl, 'ID', node.id); addPair(dl, 'Type', node.type);
  if (node.tags && node.tags.length) addPair(dl, 'Tags', node.tags.join(', '));
  for (const [key, value] of Object.entries(node.attributes || {{}})) addPair(dl, key, value);

  const relations = GRAPH_DATA.edges.filter(edge => edge.from === id || edge.to === id);
  const relationPanel = detail.appendChild(el('div', 'panel'));
  text(relationPanel.appendChild(el('div', 'eyebrow')), `Direct relationships · ${{relations.length}}`);
  const list = relationPanel.appendChild(el('div', 'relations'));
  if (!relations.length) text(list.appendChild(el('p', 'muted')), 'No direct relationships.');
  for (const edge of relations) {{
    const outgoing = edge.from === id; const otherId = outgoing ? edge.to : edge.from; const other = byId.get(otherId);
    const row = list.appendChild(el('div', 'relation'));
    text(row, outgoing ? `→ ${{edge.label || edge.type}} → ${{other ? other.title : otherId}} (${{otherId}})` : `← ${{edge.label || edge.type}} ← ${{other ? other.title : otherId}} (${{otherId}})`);
  }}
}}

search.addEventListener('input', renderList); typeFilter.addEventListener('change', renderList); renderList();
</script>
</body>
</html>
"""


def write_html(graph: Graph, output_path: str | Path, title: str | None = None) -> None:
    Path(output_path).write_text(render_html(graph, title=title), encoding="utf-8")
