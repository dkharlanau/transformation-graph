from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from .html_export import render_html
from .model import Graph
from .traceability import (
    ROLE_PRESETS,
    render_traceability_csv,
    render_traceability_markdown,
    role_traceability,
)


def _normalize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    return base_url.rstrip("/") + "/"


def _landing_html(graph: Graph, title: str, base_url: str | None) -> str:
    description = str(
        graph.project.get("description")
        or "Explore a Git-native enterprise transformation graph with traceability across processes, systems, data, interfaces, mappings, tests, changes, decisions, ownership, and evidence."
    ).strip()
    canonical = f'<link rel="canonical" href="{escape(base_url)}">' if base_url else ""
    stats = graph.stats()
    type_rows = "".join(
        f"<tr><td><code>{escape(node_type)}</code></td><td>{count}</td></tr>"
        for node_type, count in stats["node_types"].items()
    )
    role_cards = "".join(
        f'<a class="card" href="roles/{escape(role)}.html"><strong>{escape(role.title())}</strong><span>{escape(spec["description"])}</span></a>'
        for role, spec in sorted(ROLE_PRESETS.items())
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Transformation Graph</title>
  <meta name="description" content="{escape(description)}">
  {canonical}
  <style>
    :root {{ color-scheme: light dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: Canvas; color: CanvasText; }}
    main {{ width: min(1080px, calc(100% - 36px)); margin: 0 auto; padding: 64px 0 80px; }}
    h1 {{ font-size: clamp(38px, 7vw, 74px); letter-spacing: -0.055em; line-height: .98; margin: 12px 0 20px; max-width: 900px; }}
    h2 {{ margin-top: 54px; font-size: 26px; letter-spacing: -0.03em; }}
    p {{ max-width: 780px; font-size: 18px; line-height: 1.6; }}
    .eyebrow {{ text-transform: uppercase; letter-spacing: .12em; font-size: 12px; opacity: .62; }}
    .actions, .cards {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 24px; }}
    .button, .card {{ border: 1px solid color-mix(in srgb, CanvasText 18%, transparent); border-radius: 14px; color: inherit; text-decoration: none; }}
    .button {{ padding: 12px 16px; font-weight: 650; }}
    .card {{ padding: 18px; flex: 1 1 250px; min-height: 116px; }}
    .card strong, .card span {{ display: block; }}
    .card span {{ margin-top: 8px; opacity: .7; line-height: 1.45; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 38px; }}
    .metric {{ padding: 18px; border: 1px solid color-mix(in srgb, CanvasText 15%, transparent); border-radius: 14px; }}
    .metric strong {{ display: block; font-size: 30px; }}
    table {{ border-collapse: collapse; width: min(620px, 100%); }}
    th, td {{ text-align: left; padding: 9px 12px; border-bottom: 1px solid color-mix(in srgb, CanvasText 12%, transparent); }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    footer {{ margin-top: 64px; opacity: .6; font-size: 14px; }}
    @media (max-width: 700px) {{ .metrics {{ grid-template-columns: 1fr; }} main {{ padding-top: 36px; }} }}
  </style>
</head>
<body>
<main>
  <div class="eyebrow">Git-native enterprise transformation model</div>
  <h1>{escape(title)}</h1>
  <p>{escape(description)}</p>
  <div class="actions">
    <a class="button" href="explorer.html">Open interactive graph</a>
    <a class="button" href="graph.json">Canonical JSON</a>
    <a class="button" href="llms.txt">Agent / LLM index</a>
  </div>
  <div class="metrics">
    <div class="metric"><strong>{stats['nodes']}</strong><span>nodes</span></div>
    <div class="metric"><strong>{stats['edges']}</strong><span>relationships</span></div>
    <div class="metric"><strong>{len(stats['node_types'])}</strong><span>node types</span></div>
  </div>

  <h2>Role-oriented views</h2>
  <p>Each view uses deterministic shortest-path traceability rather than generated prose.</p>
  <div class="cards">{role_cards}</div>

  <h2>Graph inventory</h2>
  <table><thead><tr><th>Node type</th><th>Count</th></tr></thead><tbody>{type_rows}</tbody></table>

  <h2>Machine-readable artifacts</h2>
  <p><a href="manifest.json">manifest.json</a> · <a href="catalog.json">catalog.json</a> · <a href="graph.json">graph.json</a> · <a href="llms.txt">llms.txt</a></p>
  <footer>Generated deterministically by Transformation Graph.</footer>
</main>
</body>
</html>
"""


def _role_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td><code>{escape(row['source']['id'])}</code></td>"
        f"<td><code>{escape(row['target']['id'])}</code></td>"
        f"<td>{row['hops']}</td>"
        f"<td><code>{escape(row['path_text'])}</code></td>"
        "</tr>"
        for row in report["rows"]
    )
    if not rows:
        rows = '<tr><td colspan="4">No matching paths in this graph.</td></tr>'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(report['role'].title())} traceability · Transformation Graph</title>
<style>:root{{color-scheme:light dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}}body{{margin:0;background:Canvas;color:CanvasText}}main{{width:min(1180px,calc(100% - 32px));margin:auto;padding:42px 0}}a{{color:inherit}}p{{max-width:760px;line-height:1.55}}table{{width:100%;border-collapse:collapse;margin-top:24px}}th,td{{text-align:left;padding:9px 10px;border-bottom:1px solid color-mix(in srgb,CanvasText 14%,transparent);vertical-align:top}}code{{overflow-wrap:anywhere}}.muted{{opacity:.65}}</style></head>
<body><main><a href="../index.html">← Project</a><h1>{escape(report['role'].title())} traceability</h1><p>{escape(report['description'])}</p><p class="muted">{report['summary']['paths']} deterministic paths · max depth {report['max_depth']}</p><table><thead><tr><th>Source</th><th>Target</th><th>Hops</th><th>Path</th></tr></thead><tbody>{rows}</tbody></table><p><a href="{escape(report['role'])}.json">JSON</a> · <a href="{escape(report['role'])}.csv">CSV</a> · <a href="{escape(report['role'])}.md">Markdown</a></p></main></body></html>
"""


def _llms_text(graph: Graph) -> str:
    description = str(graph.project.get("description") or "Project-scoped enterprise transformation graph.").strip()
    roles = "\n".join(
        f"- {role}: roles/{role}.json — {spec['description']}"
        for role, spec in sorted(ROLE_PRESETS.items())
    )
    node_types = ", ".join(graph.stats()["node_types"].keys())
    return f"""# {graph.project.get('name')} — Transformation Graph

{description}

## Canonical data
- graph.json — complete canonical graph
- catalog.json — compact node and relation inventory
- manifest.json — generated artifact manifest
- explorer.html — interactive human explorer

## Role-oriented deterministic traceability
{roles}

## Query semantics
Node IDs are stable project identifiers. Edges are explicit typed relationships. Role views contain shortest dependency paths, not model-generated inferences. For bounded AI context, select a stable node and traverse only required neighbors.

Node types present: {node_types}
"""


def build_site(
    graph: Graph,
    output_dir: str | Path,
    title: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Generate a portable static site bundle from one validated graph."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    roles_dir = output / "roles"
    roles_dir.mkdir(exist_ok=True)
    page_title = title or str(graph.project.get("name") or graph.project.get("id") or "Transformation Graph")
    normalized_url = _normalize_base_url(base_url)

    (output / "index.html").write_text(_landing_html(graph, page_title, normalized_url), encoding="utf-8")
    (output / "explorer.html").write_text(render_html(graph, title=page_title), encoding="utf-8")
    (output / "graph.json").write_text(json.dumps(graph.as_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    catalog = {
        "project": graph.project,
        "stats": graph.stats(),
        "nodes": [
            {"id": node.id, "type": node.type, "title": node.title}
            for node in sorted(graph.nodes.values(), key=lambda item: item.id)
        ],
        "relations": sorted({edge.type for edge in graph.edges}),
    }
    (output / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    role_artifacts: dict[str, dict[str, str]] = {}
    for role in sorted(ROLE_PRESETS):
        report = role_traceability(graph, role, max_depth=4)
        paths = {
            "html": f"roles/{role}.html",
            "json": f"roles/{role}.json",
            "markdown": f"roles/{role}.md",
            "csv": f"roles/{role}.csv",
        }
        role_artifacts[role] = paths
        (roles_dir / f"{role}.html").write_text(_role_html(report), encoding="utf-8")
        (roles_dir / f"{role}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        (roles_dir / f"{role}.md").write_text(render_traceability_markdown(report), encoding="utf-8")
        (roles_dir / f"{role}.csv").write_text(render_traceability_csv(report), encoding="utf-8")

    manifest: dict[str, Any] = {
        "format": "transformation-graph-site",
        "version": "0.1",
        "project": graph.project,
        "stats": graph.stats(),
        "base_url": normalized_url,
        "artifacts": {
            "landing": "index.html",
            "explorer": "explorer.html",
            "graph": "graph.json",
            "catalog": "catalog.json",
            "llms": "llms.txt",
            "roles": role_artifacts,
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (output / "llms.txt").write_text(_llms_text(graph), encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")

    robots = "User-agent: *\nAllow: /\n"
    if normalized_url:
        robots += f"Sitemap: {normalized_url}sitemap.xml\n"
        urls = [normalized_url, normalized_url + "explorer.html"] + [normalized_url + f"roles/{role}.html" for role in sorted(ROLE_PRESETS)]
        sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{escape(url)}</loc></url>\n" for url in urls) + "</urlset>\n"
        (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (output / "robots.txt").write_text(robots, encoding="utf-8")
    return manifest
