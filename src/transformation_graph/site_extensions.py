from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .governance_views import build_governance_view, render_governance_view
from .graphml import write_graphml
from .model import Graph

VIEW_NAMES = ("ownership", "test-coverage", "change-readiness")


def _governance_index(reports: dict[str, dict[str, Any]]) -> str:
    cards = "".join(
        f'<a class="card" href="views/{name}.html"><strong>{report["label"]}</strong><span>{report["description"]}</span></a>'
        for name, report in reports.items()
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Governance views · Transformation Graph</title><style>:root{{color-scheme:light dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}}body{{margin:0;background:Canvas;color:CanvasText}}main{{width:min(1000px,calc(100% - 32px));margin:auto;padding:42px 0}}a{{color:inherit}}h1{{font-size:clamp(38px,7vw,64px);letter-spacing:-.05em}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:28px}}.card{{padding:20px;border:1px solid color-mix(in srgb,CanvasText 16%,transparent);border-radius:14px;text-decoration:none}}.card strong,.card span{{display:block}}.card span{{margin-top:8px;opacity:.7;line-height:1.45}}</style></head><body><main><a href="index.html">← Project</a><h1>Governance views</h1><p>Focused deterministic views for ownership, test coverage, and change readiness.</p><div class="cards">{cards}</div></main></body></html>"""


def augment_site(graph: Graph, output_dir: str | Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Add interoperable and governance-focused artifacts to a generated site bundle."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    views_dir = output / "views"
    views_dir.mkdir(exist_ok=True)

    write_graphml(graph, output / "graph.graphml")
    reports: dict[str, dict[str, Any]] = {}
    view_artifacts: dict[str, dict[str, str]] = {}
    for name in VIEW_NAMES:
        report = build_governance_view(graph, name)
        reports[name] = report
        (views_dir / f"{name}.json").write_text(render_governance_view(report, "json"), encoding="utf-8")
        (views_dir / f"{name}.html").write_text(render_governance_view(report, "html"), encoding="utf-8")
        view_artifacts[name] = {"html": f"views/{name}.html", "json": f"views/{name}.json"}
    (output / "governance.html").write_text(_governance_index(reports), encoding="utf-8")

    updated = dict(manifest)
    updated["version"] = "0.3"
    artifacts = dict(updated.get("artifacts", {}))
    artifacts["graphml"] = "graph.graphml"
    artifacts["governance"] = "governance.html"
    artifacts["governance_views"] = view_artifacts
    updated["artifacts"] = artifacts
    (output / "manifest.json").write_text(json.dumps(updated, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    llms_path = output / "llms.txt"
    llms = llms_path.read_text(encoding="utf-8") if llms_path.exists() else ""
    addition = """

## Interoperability
- graph.graphml — standards-oriented directed GraphML export; canonical stable IDs are stored as node data.

## Focused governance views
- views/ownership.json — nearest-owner traces and ownership gaps
- views/test-coverage.json — nearest-test traces and test gaps
- views/change-readiness.json — per-change owner/test/system/interface/mapping/evidence readiness
"""
    if "## Interoperability" not in llms:
        llms_path.write_text(llms.rstrip() + addition + "\n", encoding="utf-8")

    index_path = output / "index.html"
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
        marker = "<footer>Generated deterministically by Transformation Graph.</footer>"
        section = '<h2>Focused governance views</h2><p><a href="governance.html">Ownership · test coverage · change readiness</a> · <a href="graph.graphml">GraphML export</a></p>'
        if marker in text and "governance.html" not in text:
            text = text.replace(marker, section + marker)
            index_path.write_text(text, encoding="utf-8")
    return updated
