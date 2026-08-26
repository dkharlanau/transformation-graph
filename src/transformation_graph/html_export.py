from __future__ import annotations

from html import escape
from pathlib import Path
import json

from .model import Graph


def render_html(graph: Graph, title: str | None = None) -> str:
    """Render a dependency-free single-file explorer with an interactive SVG graph."""
    page_title = title or str(graph.project.get("name") or graph.project.get("id") or "Transformation Graph")
    payload = {
        "project": graph.project,
        "stats": graph.stats(),
        "nodes": [graph.nodes[node_id].as_dict() for node_id in sorted(graph.nodes)],
        "edges": sorted((edge.as_dict() for edge in graph.edges), key=lambda item: (item["from"], item["to"], item["type"], item.get("label", ""))),
    }
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    safe_title = escape(page_title)
    template = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__ · Transformation Graph</title>
  <style>
    :root { color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    * { box-sizing: border-box; }
    body { margin: 0; background: Canvas; color: CanvasText; }
    header { padding: 24px 28px 18px; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); }
    h1 { margin: 0 0 6px; font-size: clamp(24px, 3vw, 38px); letter-spacing: -.03em; }
    h2 { font-size: clamp(22px, 2.5vw, 32px); margin: 6px 0 10px; letter-spacing: -.025em; }
    .muted { opacity: .68; }
    .eyebrow { text-transform: uppercase; letter-spacing: .08em; font-size: 12px; opacity: .6; }
    .stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 16px; max-width: 760px; }
    .stat { padding: 10px 13px; border: 1px solid color-mix(in srgb, CanvasText 14%, transparent); border-radius: 11px; }
    .stat strong { display: block; font-size: 21px; }
    .workspace { display: grid; grid-template-columns: minmax(250px, 330px) minmax(0, 1fr); min-height: calc(100vh - 160px); }
    aside { border-right: 1px solid color-mix(in srgb, CanvasText 15%, transparent); padding: 16px; max-height: calc(100vh - 160px); overflow: auto; }
    .controls { display: grid; gap: 9px; position: sticky; top: -16px; z-index: 4; background: Canvas; padding: 16px 0 12px; }
    input, select, button { font: inherit; }
    input, select { width: 100%; padding: 9px 11px; border-radius: 9px; border: 1px solid color-mix(in srgb, CanvasText 22%, transparent); background: Canvas; color: CanvasText; }
    button { color: CanvasText; }
    #nodeList { display: grid; gap: 6px; }
    button.node { text-align: left; padding: 9px 10px; border-radius: 9px; border: 1px solid transparent; background: color-mix(in srgb, CanvasText 5%, transparent); cursor: pointer; }
    button.node:hover, button.node.active { border-color: color-mix(in srgb, CanvasText 25%, transparent); background: color-mix(in srgb, CanvasText 9%, transparent); }
    button.node small { display: block; opacity: .62; margin-top: 2px; overflow-wrap: anywhere; }
    .content { min-width: 0; display: grid; grid-template-rows: minmax(380px, 55vh) auto; }
    .canvas-shell { position: relative; overflow: auto; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); background: color-mix(in srgb, CanvasText 2.5%, transparent); }
    .canvas-toolbar { position: sticky; left: 14px; top: 12px; z-index: 3; display: inline-flex; gap: 8px; align-items: center; padding: 7px 9px; margin: 12px; border: 1px solid color-mix(in srgb, CanvasText 14%, transparent); border-radius: 10px; background: color-mix(in srgb, Canvas 92%, transparent); backdrop-filter: blur(8px); }
    .canvas-toolbar button { border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 8px; background: Canvas; padding: 6px 9px; cursor: pointer; }
    #graphView { display: block; min-width: 100%; }
    .graph-edge { fill: none; stroke: color-mix(in srgb, CanvasText 22%, transparent); stroke-width: 1.2; transition: opacity .12s, stroke-width .12s; }
    .graph-edge.dim { opacity: .08; }
    .graph-edge.active { opacity: .9; stroke-width: 2.2; }
    .graph-node rect { fill: Canvas; stroke: color-mix(in srgb, CanvasText 22%, transparent); stroke-width: 1; rx: 9; cursor: pointer; transition: opacity .12s, stroke-width .12s; }
    .graph-node text { fill: CanvasText; pointer-events: none; font-size: 12px; }
    .graph-node .node-id { opacity: .58; font-size: 10px; }
    .graph-node.dim { opacity: .18; }
    .graph-node.active rect { stroke-width: 2.6; }
    .column-label { fill: CanvasText; opacity: .56; font-size: 11px; letter-spacing: .08em; }
    section.detail { padding: 24px 28px 36px; max-width: 1100px; }
    .panel { border: 1px solid color-mix(in srgb, CanvasText 14%, transparent); border-radius: 14px; padding: 15px; margin: 16px 0; }
    dl { display: grid; grid-template-columns: 140px minmax(0, 1fr); gap: 8px 14px; margin: 0; }
    dt { opacity: .62; } dd { margin: 0; overflow-wrap: anywhere; }
    .relations { display: grid; gap: 7px; margin-top: 10px; }
    button.relation { text-align: left; border: 0; padding: 9px 11px; border-radius: 9px; background: color-mix(in srgb, CanvasText 5%, transparent); cursor: pointer; }
    button.relation:hover { background: color-mix(in srgb, CanvasText 9%, transparent); }
    code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: .92em; }
    @media (max-width: 800px) { .stats { grid-template-columns: repeat(2, 1fr); } .workspace { grid-template-columns: 1fr; } aside { border-right: 0; border-bottom: 1px solid color-mix(in srgb, CanvasText 15%, transparent); max-height: 310px; } .content { grid-template-rows: minmax(340px, 52vh) auto; } section.detail { padding: 20px 18px 30px; } }
  </style>
</head>
<body>
<header>
  <div class="eyebrow">Transformation Graph</div>
  <h1>__TITLE__</h1>
  <div class="muted" id="projectDescription"></div>
  <div class="stats">
    <div class="stat"><strong id="nodeCount">0</strong><span class="muted">nodes</span></div>
    <div class="stat"><strong id="edgeCount">0</strong><span class="muted">relations</span></div>
    <div class="stat"><strong id="typeCount">0</strong><span class="muted">node types</span></div>
    <div class="stat"><strong id="relationCount">0</strong><span class="muted">relation types</span></div>
  </div>
</header>
<div class="workspace">
  <aside>
    <div class="controls">
      <input id="search" type="search" placeholder="Search nodes…" aria-label="Search nodes">
      <select id="typeFilter" aria-label="Filter by node type"><option value="">All node types</option></select>
      <div class="muted" id="visibleCount"></div>
    </div>
    <div id="nodeList"></div>
  </aside>
  <div class="content">
    <div class="canvas-shell">
      <div class="canvas-toolbar"><strong>Graph</strong><span class="muted" id="canvasCount"></span><button id="resetSelection" type="button">Reset</button></div>
      <svg id="graphView" role="img" aria-label="Transformation dependency graph"></svg>
    </div>
    <section class="detail" id="detail"><div class="eyebrow">Select a node</div><h2>Explore transformation dependencies</h2><p class="muted">Search or filter the inventory, then select a node in the list or graph to inspect its attributes and relationships.</p></section>
  </div>
</div>
<script>
const GRAPH_DATA = __DATA__;
const byId = new Map(GRAPH_DATA.nodes.map(node => [node.id, node]));
const search = document.getElementById('search');
const typeFilter = document.getElementById('typeFilter');
const nodeList = document.getElementById('nodeList');
const detail = document.getElementById('detail');
const svg = document.getElementById('graphView');
let selectedId = null;
let visibleIds = new Set(GRAPH_DATA.nodes.map(node => node.id));
document.getElementById('projectDescription').textContent = GRAPH_DATA.project.description || GRAPH_DATA.project.id || '';
document.getElementById('nodeCount').textContent = GRAPH_DATA.nodes.length;
document.getElementById('edgeCount').textContent = GRAPH_DATA.edges.length;
document.getElementById('typeCount').textContent = Object.keys(GRAPH_DATA.stats.node_types || {}).length;
document.getElementById('relationCount').textContent = Object.keys(GRAPH_DATA.stats.edge_types || {}).length;
for (const type of [...new Set(GRAPH_DATA.nodes.map(node => node.type))].sort()) { const option = document.createElement('option'); option.value = type; option.textContent = type; typeFilter.appendChild(option); }
function text(element, value) { element.textContent = value == null ? '' : String(value); return element; }
function el(name, className) { const element = document.createElement(name); if (className) element.className = className; return element; }
function svgEl(name, attrs = {}) { const element = document.createElementNS('http://www.w3.org/2000/svg', name); for (const [key, value] of Object.entries(attrs)) element.setAttribute(key, String(value)); return element; }
function filteredNodes() { const query = search.value.trim().toLowerCase(); const type = typeFilter.value; return GRAPH_DATA.nodes.filter(node => (!type || node.type === type) && (!query || `${node.id} ${node.title} ${node.type} ${node.description || ''}`.toLowerCase().includes(query))); }
function renderList(nodes) { nodeList.replaceChildren(); document.getElementById('visibleCount').textContent = `${nodes.length} of ${GRAPH_DATA.nodes.length} nodes`; for (const node of nodes) { const button = el('button', 'node' + (node.id === selectedId ? ' active' : '')); button.type = 'button'; button.addEventListener('click', () => selectNode(node.id)); text(button.appendChild(el('div')), node.title); text(button.appendChild(el('small')), `${node.type} · ${node.id}`); nodeList.appendChild(button); } }
function renderGraph(nodes) {
  visibleIds = new Set(nodes.map(node => node.id)); svg.replaceChildren();
  const types = [...new Set(nodes.map(node => node.type))].sort(); const grouped = new Map(types.map(type => [type, nodes.filter(node => node.type === type)]));
  const columnWidth = 230, rowHeight = 84, boxWidth = 184, boxHeight = 54, marginX = 48, marginY = 58;
  const maxRows = Math.max(1, ...[...grouped.values()].map(items => items.length)); const width = Math.max(720, marginX * 2 + Math.max(1, types.length) * columnWidth); const height = Math.max(330, marginY + maxRows * rowHeight + 40);
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`); svg.setAttribute('width', width); svg.setAttribute('height', height);
  const defs = svg.appendChild(svgEl('defs')); const marker = defs.appendChild(svgEl('marker', {id:'arrow', viewBox:'0 0 10 10', refX:9, refY:5, markerWidth:6, markerHeight:6, orient:'auto-start-reverse'})); marker.appendChild(svgEl('path', {d:'M 0 0 L 10 5 L 0 10 z', fill:'currentColor', opacity:'.35'}));
  const positions = new Map(); types.forEach((type, column) => { const x = marginX + column * columnWidth; const label = svg.appendChild(svgEl('text', {x, y:27, class:'column-label'})); label.textContent = type; grouped.get(type).forEach((node, row) => positions.set(node.id, {x, y:marginY + row * rowHeight})); });
  const edgeLayer = svg.appendChild(svgEl('g', {id:'edgeLayer'}));
  for (const edge of GRAPH_DATA.edges) { if (!positions.has(edge.from) || !positions.has(edge.to)) continue; const a = positions.get(edge.from), b = positions.get(edge.to); const x1 = a.x + boxWidth, y1 = a.y + boxHeight / 2, x2 = b.x, y2 = b.y + boxHeight / 2, bend = Math.max(34, Math.abs(x2 - x1) * .42); const path = edgeLayer.appendChild(svgEl('path', {d:`M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`, class:'graph-edge', 'marker-end':'url(#arrow)', 'data-from':edge.from, 'data-to':edge.to})); const title = path.appendChild(svgEl('title')); title.textContent = edge.label || edge.type; }
  const nodeLayer = svg.appendChild(svgEl('g', {id:'nodeLayer'}));
  for (const node of nodes) { const pos = positions.get(node.id); const group = nodeLayer.appendChild(svgEl('g', {class:'graph-node' + (node.id === selectedId ? ' active' : ''), transform:`translate(${pos.x} ${pos.y})`, 'data-id':node.id})); group.addEventListener('click', () => selectNode(node.id)); group.appendChild(svgEl('rect', {width:boxWidth, height:boxHeight})); const title = group.appendChild(svgEl('text', {x:11, y:21})); title.textContent = node.title.length > 25 ? node.title.slice(0, 24) + '…' : node.title; const idText = group.appendChild(svgEl('text', {x:11, y:40, class:'node-id'})); idText.textContent = node.id.length > 29 ? node.id.slice(0, 28) + '…' : node.id; const tooltip = group.appendChild(svgEl('title')); tooltip.textContent = `${node.title}\n${node.type} · ${node.id}`; }
  document.getElementById('canvasCount').textContent = `${nodes.length} nodes`; updateGraphSelection();
}
function addPair(dl, key, value) { text(dl.appendChild(el('dt')), key); const dd = dl.appendChild(el('dd')); if (typeof value === 'object' && value !== null) text(dd.appendChild(el('code')), JSON.stringify(value)); else text(dd, value); }
function selectNode(id) {
  selectedId = id; const nodes = filteredNodes(); renderList(nodes); if (!visibleIds.has(id)) { search.value = ''; typeFilter.value = ''; renderAll(); } else updateGraphSelection();
  const node = byId.get(id); detail.replaceChildren(); text(detail.appendChild(el('div', 'eyebrow')), node.type); text(detail.appendChild(el('h2')), node.title); if (node.description) text(detail.appendChild(el('p', 'muted')), node.description);
  const panel = detail.appendChild(el('div', 'panel')); const dl = panel.appendChild(el('dl')); addPair(dl, 'ID', node.id); addPair(dl, 'Type', node.type); if (node.tags && node.tags.length) addPair(dl, 'Tags', node.tags.join(', ')); for (const [key, value] of Object.entries(node.attributes || {})) addPair(dl, key, value);
  const relations = GRAPH_DATA.edges.filter(edge => edge.from === id || edge.to === id); const relationPanel = detail.appendChild(el('div', 'panel')); text(relationPanel.appendChild(el('div', 'eyebrow')), `Direct relationships · ${relations.length}`); const list = relationPanel.appendChild(el('div', 'relations')); if (!relations.length) text(list.appendChild(el('p', 'muted')), 'No direct relationships.');
  for (const edge of relations) { const outgoing = edge.from === id; const otherId = outgoing ? edge.to : edge.from; const other = byId.get(otherId); const button = list.appendChild(el('button', 'relation')); button.type = 'button'; text(button, outgoing ? `→ ${edge.label || edge.type} → ${other ? other.title : otherId} (${otherId})` : `← ${edge.label || edge.type} ← ${other ? other.title : otherId} (${otherId})`); if (other) button.addEventListener('click', () => selectNode(otherId)); }
}
function updateGraphSelection() { const nodes = svg.querySelectorAll('.graph-node'), edges = svg.querySelectorAll('.graph-edge'); if (!selectedId) { nodes.forEach(item => item.classList.remove('dim','active')); edges.forEach(item => item.classList.remove('dim','active')); return; } const neighbors = new Set([selectedId]); for (const edge of GRAPH_DATA.edges) { if (edge.from === selectedId) neighbors.add(edge.to); if (edge.to === selectedId) neighbors.add(edge.from); } nodes.forEach(item => { const id = item.getAttribute('data-id'); item.classList.toggle('active', id === selectedId); item.classList.toggle('dim', !neighbors.has(id)); }); edges.forEach(item => { const active = item.getAttribute('data-from') === selectedId || item.getAttribute('data-to') === selectedId; item.classList.toggle('active', active); item.classList.toggle('dim', !active); }); }
function renderAll() { const nodes = filteredNodes(); renderList(nodes); renderGraph(nodes); }
search.addEventListener('input', renderAll); typeFilter.addEventListener('change', renderAll); document.getElementById('resetSelection').addEventListener('click', () => { selectedId = null; detail.innerHTML = '<div class="eyebrow">Select a node</div><h2>Explore transformation dependencies</h2><p class="muted">Select a node in the list or graph to inspect its attributes and relationships.</p>'; renderAll(); }); renderAll();
</script>
</body>
</html>
'''
    return template.replace("__TITLE__", safe_title).replace("__DATA__", data)


def write_html(graph: Graph, output_path: str | Path, title: str | None = None) -> None:
    Path(output_path).write_text(render_html(graph, title=title), encoding="utf-8")
