from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any, Literal

from .model import Graph, GraphValidationError

GovernanceViewName = Literal["ownership", "test-coverage", "change-readiness"]
GovernanceViewFormat = Literal["json", "html"]

VIEW_SPECS: dict[str, dict[str, Any]] = {
    "ownership": {
        "label": "Ownership traceability",
        "description": "Processes, interfaces, decisions, and changes traced to the nearest explicit owner.",
        "source_types": {"process", "interface", "decision", "change"},
        "target_types": {"owner"},
        "max_depth": 4,
    },
    "test-coverage": {
        "label": "Test coverage traceability",
        "description": "Changes, requirements, interfaces, mappings, and process steps traced to the nearest test.",
        "source_types": {"change", "requirement", "interface", "mapping", "process_step"},
        "target_types": {"test"},
        "max_depth": 3,
    },
}

CHANGE_DIMENSIONS: tuple[dict[str, Any], ...] = (
    {"id": "owner", "label": "Owner", "target_types": {"owner"}, "max_depth": 4},
    {"id": "test", "label": "Test", "target_types": {"test"}, "max_depth": 2},
    {"id": "system", "label": "System", "target_types": {"system"}, "max_depth": 3},
    {"id": "interface", "label": "Interface", "target_types": {"interface"}, "max_depth": 3},
    {"id": "mapping", "label": "Mapping", "target_types": {"mapping"}, "max_depth": 3},
    {"id": "evidence", "label": "Evidence", "target_types": {"evidence"}, "max_depth": 4},
)


def _nearest(graph: Graph, source_id: str, target_types: set[str], max_depth: int) -> dict[str, Any] | None:
    candidates: list[tuple[int, list[str], str]] = []
    for target in sorted(node.id for node in graph.nodes.values() if node.type in target_types and node.id != source_id):
        path = graph.path(source_id, target, undirected=True)
        if path is None:
            continue
        hops = len(path) - 1
        if hops <= max_depth:
            candidates.append((hops, path, target))
    if not candidates:
        return None
    hops, path, target = sorted(candidates, key=lambda item: (item[0], item[1], item[2]))[0]
    node = graph.nodes[target]
    return {"target": {"id": node.id, "type": node.type, "title": node.title}, "hops": hops, "path": path}


def _coverage_view(graph: Graph, view: str, spec: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for node in sorted((node for node in graph.nodes.values() if node.type in spec["source_types"]), key=lambda item: item.id):
        nearest = _nearest(graph, node.id, set(spec["target_types"]), int(spec["max_depth"]))
        rows.append({
            "source": {"id": node.id, "type": node.type, "title": node.title},
            "covered": nearest is not None,
            **({"trace": nearest} if nearest else {}),
        })
    covered = sum(row["covered"] for row in rows)
    total = len(rows)
    return {
        "view": view,
        "label": spec["label"],
        "description": spec["description"],
        "project": graph.project.get("id"),
        "max_depth": spec["max_depth"],
        "summary": {"total": total, "covered": covered, "gaps": total - covered, "coverage": None if total == 0 else round(100 * covered / total, 1)},
        "rows": rows,
    }


def _change_readiness(graph: Graph) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for change in sorted((node for node in graph.nodes.values() if node.type == "change"), key=lambda item: item.id):
        dimensions: list[dict[str, Any]] = []
        for spec in CHANGE_DIMENSIONS:
            trace = _nearest(graph, change.id, set(spec["target_types"]), int(spec["max_depth"]))
            dimensions.append({
                "id": spec["id"],
                "label": spec["label"],
                "ready": trace is not None,
                "max_depth": spec["max_depth"],
                **({"trace": trace} if trace else {}),
            })
        ready = sum(item["ready"] for item in dimensions)
        rows.append({
            "change": {"id": change.id, "title": change.title},
            "readiness": round(100 * ready / len(dimensions), 1),
            "ready_dimensions": ready,
            "total_dimensions": len(dimensions),
            "dimensions": dimensions,
        })
    average = None if not rows else round(sum(row["readiness"] for row in rows) / len(rows), 1)
    gaps = sum(item["total_dimensions"] - item["ready_dimensions"] for item in rows)
    return {
        "view": "change-readiness",
        "label": "Change readiness traceability",
        "description": "Each change is checked for bounded traces to ownership, tests, systems, interfaces, mappings, and evidence.",
        "project": graph.project.get("id"),
        "summary": {"changes": len(rows), "average_readiness": average, "gaps": gaps},
        "dimensions": [{"id": item["id"], "label": item["label"], "max_depth": item["max_depth"]} for item in CHANGE_DIMENSIONS],
        "rows": rows,
    }


def build_governance_view(graph: Graph, view: GovernanceViewName | str) -> dict[str, Any]:
    if view == "change-readiness":
        return _change_readiness(graph)
    if view in VIEW_SPECS:
        return _coverage_view(graph, view, VIEW_SPECS[view])
    raise GraphValidationError(f"unknown governance view '{view}'; expected: ownership, test-coverage, change-readiness")


def _coverage_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td><code>{escape(row['source']['id'])}</code><br><span class='muted'>{escape(row['source']['title'])}</span></td>"
        f"<td>{'covered' if row['covered'] else 'gap'}</td>"
        f"<td>{escape(row.get('trace', {}).get('target', {}).get('title', '—'))}</td>"
        f"<td>{row.get('trace', {}).get('hops', '—')}</td>"
        f"<td><code>{escape(' → '.join(row.get('trace', {}).get('path', [])) or '—')}</code></td>"
        "</tr>"
        for row in report["rows"]
    ) or '<tr><td colspan="5">No applicable source nodes.</td></tr>'
    summary = report["summary"]
    coverage = "N/A" if summary["coverage"] is None else f"{summary['coverage']}%"
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(report['label'])} · Transformation Graph</title><style>:root{{color-scheme:light dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}}body{{margin:0;background:Canvas;color:CanvasText}}main{{width:min(1180px,calc(100% - 32px));margin:auto;padding:42px 0}}a{{color:inherit}}h1{{font-size:clamp(34px,6vw,58px);letter-spacing:-.045em}}.metric{{font-size:34px;font-weight:750}}.muted{{opacity:.65}}table{{width:100%;border-collapse:collapse;margin-top:28px}}th,td{{text-align:left;padding:9px 10px;border-bottom:1px solid color-mix(in srgb,CanvasText 14%,transparent);vertical-align:top}}code{{overflow-wrap:anywhere}}</style></head><body><main><a href="../index.html">← Project</a><h1>{escape(report['label'])}</h1><p>{escape(report['description'])}</p><div class="metric">{coverage}</div><p class="muted">{summary['covered']} covered · {summary['gaps']} gaps · {summary['total']} applicable nodes</p><table><thead><tr><th>Source</th><th>Status</th><th>Nearest target</th><th>Hops</th><th>Path</th></tr></thead><tbody>{rows}</tbody></table></main></body></html>"""


def _change_html(report: dict[str, Any]) -> str:
    body = []
    for row in report["rows"]:
        dimensions = "".join(f"<li><strong>{escape(item['label'])}</strong>: {'ready' if item['ready'] else 'gap'}" + (f" — <code>{escape(' → '.join(item['trace']['path']))}</code>" if item.get('trace') else "") + "</li>" for item in row["dimensions"])
        body.append(f"<section><h2>{escape(row['change']['title'])}</h2><div class='metric'>{row['readiness']}%</div><code>{escape(row['change']['id'])}</code><ul>{dimensions}</ul></section>")
    sections = "".join(body) or "<p>No change nodes in this graph.</p>"
    average = report["summary"]["average_readiness"]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Change readiness · Transformation Graph</title><style>:root{{color-scheme:light dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif}}body{{margin:0;background:Canvas;color:CanvasText}}main{{width:min(1000px,calc(100% - 32px));margin:auto;padding:42px 0}}a{{color:inherit}}h1{{font-size:clamp(34px,6vw,58px);letter-spacing:-.045em}}section{{padding:20px 0;border-top:1px solid color-mix(in srgb,CanvasText 14%,transparent)}}.metric{{font-size:34px;font-weight:750}}code{{overflow-wrap:anywhere}}li{{margin:8px 0}}</style></head><body><main><a href="../index.html">← Project</a><h1>Change readiness traceability</h1><p>{escape(report['description'])}</p><p>Average: <strong>{'N/A' if average is None else str(average)+'%'}</strong> · gaps: <strong>{report['summary']['gaps']}</strong></p>{sections}</main></body></html>"""


def render_governance_view(report: dict[str, Any], format: GovernanceViewFormat) -> str:
    if format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if format == "html":
        return _change_html(report) if report["view"] == "change-readiness" else _coverage_html(report)
    raise GraphValidationError(f"unsupported governance view format: {format}")


def write_governance_view(report: dict[str, Any], output_path: str | Path, format: GovernanceViewFormat) -> None:
    Path(output_path).write_text(render_governance_view(report, format), encoding="utf-8")
