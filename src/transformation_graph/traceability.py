from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Literal

from .model import Graph, GraphValidationError

ReportFormat = Literal["json", "markdown", "csv"]

ROLE_PRESETS: dict[str, dict[str, Any]] = {
    "architect": {
        "description": "Cross-domain architecture traceability across processes, systems, interfaces, changes, decisions, tests, and ownership.",
        "pairs": [
            ("process", "system"),
            ("process", "interface"),
            ("change", "decision"),
            ("change", "test"),
            ("decision", "owner"),
        ],
    },
    "integration": {
        "description": "Interface-centric traceability across endpoints, mappings, tests, ownership, and transported data.",
        "pairs": [
            ("interface", "system"),
            ("interface", "mapping"),
            ("interface", "test"),
            ("interface", "owner"),
            ("interface", "data_object"),
        ],
    },
    "data": {
        "description": "Data lineage from mappings and objects down to fields, rules, evidence, and business objects.",
        "pairs": [
            ("mapping", "field"),
            ("mapping", "rule"),
            ("mapping", "evidence"),
            ("data_object", "field"),
            ("business_object", "data_object"),
        ],
    },
    "test": {
        "description": "Coverage traceability from tests to changes, interfaces, requirements, mappings, and process steps.",
        "pairs": [
            ("test", "change"),
            ("test", "interface"),
            ("test", "requirement"),
            ("test", "mapping"),
            ("test", "process_step"),
        ],
    },
    "cutover": {
        "description": "Change-centered cutover traceability across systems, interfaces, mappings, tests, and ownership.",
        "pairs": [
            ("change", "system"),
            ("change", "interface"),
            ("change", "mapping"),
            ("change", "test"),
            ("change", "owner"),
        ],
    },
}


def _relation_step(graph: Graph, left: str, right: str) -> dict[str, Any]:
    candidates = [
        edge
        for edge in graph.edges
        if (edge.source == left and edge.target == right)
        or (edge.source == right and edge.target == left)
    ]
    if not candidates:
        raise GraphValidationError(f"path contains nodes without a direct edge: {left} -> {right}")
    edge = sorted(candidates, key=lambda item: (item.type, item.label or "", item.source, item.target))[0]
    forward = edge.source == left and edge.target == right
    return {
        "type": edge.type,
        "label": edge.label,
        "traversal": "forward" if forward else "reverse",
        "edge_from": edge.source,
        "edge_to": edge.target,
    }


def _path_text(path: list[str], relations: list[dict[str, Any]]) -> str:
    if not path:
        return ""
    text = path[0]
    for index, relation in enumerate(relations):
        label = relation.get("label") or relation["type"]
        if relation["traversal"] == "forward":
            text += f" -[{label}]-> {path[index + 1]}"
        else:
            text += f" <-[{label}]- {path[index + 1]}"
    return text


def traceability_matrix(
    graph: Graph,
    source_types: set[str] | list[str] | tuple[str, ...],
    target_types: set[str] | list[str] | tuple[str, ...],
    max_depth: int = 4,
    *,
    undirected: bool = True,
) -> dict[str, Any]:
    """Return deterministic shortest-path traceability between selected node types."""
    if max_depth < 1:
        raise GraphValidationError("max_depth must be >= 1")
    source_types = {str(item) for item in source_types if str(item)}
    target_types = {str(item) for item in target_types if str(item)}
    if not source_types or not target_types:
        raise GraphValidationError("source_types and target_types must not be empty")

    sources = sorted(
        (node for node in graph.nodes.values() if node.type in source_types),
        key=lambda item: item.id,
    )
    targets = sorted(
        (node for node in graph.nodes.values() if node.type in target_types),
        key=lambda item: item.id,
    )
    rows: list[dict[str, Any]] = []

    for source in sources:
        for target in targets:
            if source.id == target.id:
                continue
            path = graph.path(source.id, target.id, undirected=undirected)
            if path is None:
                continue
            hops = len(path) - 1
            if hops > max_depth:
                continue
            relations = [
                _relation_step(graph, path[index], path[index + 1])
                for index in range(len(path) - 1)
            ]
            rows.append(
                {
                    "source": {"id": source.id, "type": source.type, "title": source.title},
                    "target": {"id": target.id, "type": target.type, "title": target.title},
                    "hops": hops,
                    "path": path,
                    "relations": relations,
                    "path_text": _path_text(path, relations),
                }
            )

    return {
        "project": graph.project.get("id"),
        "source_types": sorted(source_types),
        "target_types": sorted(target_types),
        "max_depth": max_depth,
        "undirected": undirected,
        "summary": {
            "source_nodes": len(sources),
            "target_nodes": len(targets),
            "paths": len(rows),
        },
        "rows": rows,
    }


def role_traceability(graph: Graph, role: str, max_depth: int = 4) -> dict[str, Any]:
    """Build a role-oriented traceability report from stable type-pair presets."""
    if role not in ROLE_PRESETS:
        raise GraphValidationError(
            f"unknown role '{role}'; expected one of: {', '.join(sorted(ROLE_PRESETS))}"
        )
    preset = ROLE_PRESETS[role]
    rows: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []

    for source_type, target_type in preset["pairs"]:
        report = traceability_matrix(
            graph,
            {source_type},
            {target_type},
            max_depth=max_depth,
            undirected=True,
        )
        pair_rows = report["rows"]
        rows.extend(pair_rows)
        source_ids = sorted(
            node.id for node in graph.nodes.values() if node.type == source_type
        )
        covered_sources = {row["source"]["id"] for row in pair_rows}
        coverage.append(
            {
                "source_type": source_type,
                "target_type": target_type,
                "source_nodes": len(source_ids),
                "paths": len(pair_rows),
                "uncovered_source_ids": [
                    node_id for node_id in source_ids if node_id not in covered_sources
                ],
            }
        )

    rows.sort(key=lambda row: (row["source"]["id"], row["target"]["id"], row["path_text"]))
    return {
        "project": graph.project.get("id"),
        "role": role,
        "description": preset["description"],
        "max_depth": max_depth,
        "pairs": [list(pair) for pair in preset["pairs"]],
        "summary": {
            "paths": len(rows),
            "pair_checks": len(coverage),
            "uncovered_sources": sum(len(item["uncovered_source_ids"]) for item in coverage),
        },
        "coverage": coverage,
        "rows": rows,
    }


def list_role_presets() -> dict[str, Any]:
    return {
        role: {
            "description": spec["description"],
            "pairs": [list(pair) for pair in spec["pairs"]],
        }
        for role, spec in sorted(ROLE_PRESETS.items())
    }


def _escape_markdown(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_traceability_markdown(report: dict[str, Any]) -> str:
    role = report.get("role")
    title = f"{str(role).title()} traceability" if role else "Traceability matrix"
    lines = [f"# {title}", ""]
    if report.get("description"):
        lines += [str(report["description"]), ""]
    summary = report.get("summary", {})
    lines += [
        f"- Project: `{report.get('project')}`",
        f"- Paths: **{summary.get('paths', 0)}**",
        f"- Maximum depth: **{report.get('max_depth')}**",
        "",
        "| Source | Target | Hops | Path |",
        "| --- | --- | ---: | --- |",
    ]
    for row in report.get("rows", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_markdown(f"{row['source']['title']} (`{row['source']['id']}`)"),
                    _escape_markdown(f"{row['target']['title']} (`{row['target']['id']}`)"),
                    str(row["hops"]),
                    _escape_markdown(row["path_text"]),
                ]
            )
            + " |"
        )
    if not report.get("rows"):
        lines.append("| _No matching paths_ |  |  |  |")

    if role:
        lines += ["", "## Coverage", "", "| Source type | Target type | Sources | Paths | Uncovered |", "| --- | --- | ---: | ---: | --- |"]
        for item in report.get("coverage", []):
            uncovered = ", ".join(item["uncovered_source_ids"]) or "—"
            lines.append(
                f"| {item['source_type']} | {item['target_type']} | {item['source_nodes']} | {item['paths']} | {_escape_markdown(uncovered)} |"
            )
    return "\n".join(lines) + "\n"


def render_traceability_csv(report: dict[str, Any]) -> str:
    handle = StringIO()
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "source_id",
            "source_type",
            "source_title",
            "target_id",
            "target_type",
            "target_title",
            "hops",
            "path",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    for row in report.get("rows", []):
        writer.writerow(
            {
                "source_id": row["source"]["id"],
                "source_type": row["source"]["type"],
                "source_title": row["source"]["title"],
                "target_id": row["target"]["id"],
                "target_type": row["target"]["type"],
                "target_title": row["target"]["title"],
                "hops": row["hops"],
                "path": row["path_text"],
            }
        )
    return handle.getvalue()


def render_traceability_report(report: dict[str, Any], format: ReportFormat) -> str:
    if format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if format == "markdown":
        return render_traceability_markdown(report)
    if format == "csv":
        return render_traceability_csv(report)
    raise GraphValidationError(f"unsupported traceability format: {format}")


def write_traceability_report(
    report: dict[str, Any], output_path: str | Path, format: ReportFormat
) -> None:
    Path(output_path).write_text(render_traceability_report(report, format), encoding="utf-8")
