from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from .model import Graph, GraphValidationError

ScorecardFormat = Literal["json", "markdown"]

DIMENSIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "connectivity",
        "label": "Graph connectivity",
        "weight": 15,
        "description": "Nodes connected by at least one explicit relationship.",
    },
    {
        "id": "ownership",
        "label": "Ownership traceability",
        "weight": 20,
        "description": "Processes, interfaces, and decisions traceable to an owner within four hops.",
        "source_types": {"process", "interface", "decision"},
        "target_types": {"owner"},
        "max_depth": 4,
    },
    {
        "id": "test_coverage",
        "label": "Test traceability",
        "weight": 25,
        "description": "Changes, requirements, and interfaces traceable to a test within two hops.",
        "source_types": {"change", "requirement", "interface"},
        "target_types": {"test"},
        "max_depth": 2,
    },
    {
        "id": "evidence",
        "label": "Evidence traceability",
        "weight": 15,
        "description": "Mappings and decisions traceable to evidence within three hops.",
        "source_types": {"mapping", "decision"},
        "target_types": {"evidence"},
        "max_depth": 3,
    },
    {
        "id": "system_traceability",
        "label": "System traceability",
        "weight": 10,
        "description": "Processes and interfaces traceable to systems within three hops.",
        "source_types": {"process", "interface"},
        "target_types": {"system"},
        "max_depth": 3,
    },
    {
        "id": "data_traceability",
        "label": "Data traceability",
        "weight": 15,
        "description": "Mappings and interfaces traceable to fields, data objects, or business objects within three hops.",
        "source_types": {"mapping", "interface"},
        "target_types": {"field", "data_object", "business_object"},
        "max_depth": 3,
    },
)


def _score_band(score: float) -> str:
    if score >= 90:
        return "90-100"
    if score >= 75:
        return "75-89"
    if score >= 60:
        return "60-74"
    return "0-59"


def _connectivity_dimension(graph: Graph, spec: dict[str, Any]) -> dict[str, Any]:
    connected: set[str] = set()
    for edge in graph.edges:
        connected.add(edge.source)
        connected.add(edge.target)
    candidates = sorted(graph.nodes)
    covered = [node_id for node_id in candidates if node_id in connected]
    gaps = [node_id for node_id in candidates if node_id not in connected]
    denominator = len(candidates)
    percentage = 100.0 if denominator == 0 else round(100 * len(covered) / denominator, 1)
    return {
        "id": spec["id"],
        "label": spec["label"],
        "description": spec["description"],
        "weight": spec["weight"],
        "applicable": denominator > 0,
        "numerator": len(covered),
        "denominator": denominator,
        "percentage": percentage,
        "covered": [{"id": node_id} for node_id in covered],
        "gaps": [{"id": node_id} for node_id in gaps],
    }


def _trace_dimension(graph: Graph, spec: dict[str, Any]) -> dict[str, Any]:
    source_types = set(spec["source_types"])
    target_types = set(spec["target_types"])
    max_depth = int(spec["max_depth"])
    sources = sorted(node.id for node in graph.nodes.values() if node.type in source_types)
    targets = sorted(node.id for node in graph.nodes.values() if node.type in target_types)
    covered: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    for source in sources:
        paths: list[tuple[int, list[str], str]] = []
        for target in targets:
            if source == target:
                continue
            path = graph.path(source, target, undirected=True)
            if path is None:
                continue
            hops = len(path) - 1
            if hops <= max_depth:
                paths.append((hops, path, target))
        if paths:
            hops, path, target = sorted(paths, key=lambda item: (item[0], item[1], item[2]))[0]
            covered.append({"id": source, "target": target, "hops": hops, "path": path})
        else:
            gaps.append({"id": source})

    denominator = len(sources)
    percentage = None if denominator == 0 else round(100 * len(covered) / denominator, 1)
    return {
        "id": spec["id"],
        "label": spec["label"],
        "description": spec["description"],
        "weight": spec["weight"],
        "applicable": denominator > 0,
        "source_types": sorted(source_types),
        "target_types": sorted(target_types),
        "max_depth": max_depth,
        "numerator": len(covered),
        "denominator": denominator,
        "percentage": percentage,
        "covered": covered,
        "gaps": gaps,
    }


def build_scorecard(graph: Graph) -> dict[str, Any]:
    """Build a transparent weighted governance scorecard with explicit coverage gaps."""
    dimensions: list[dict[str, Any]] = []
    for spec in DIMENSIONS:
        dimension = _connectivity_dimension(graph, spec) if spec["id"] == "connectivity" else _trace_dimension(graph, spec)
        dimensions.append(dimension)

    applicable = [item for item in dimensions if item["applicable"]]
    total_weight = sum(item["weight"] for item in applicable)
    weighted_points = 0.0
    for item in dimensions:
        if item["applicable"]:
            item["weighted_points"] = round((item["percentage"] / 100.0) * item["weight"], 2)
            weighted_points += item["weighted_points"]
        else:
            item["weighted_points"] = None
    overall = 100.0 if total_weight == 0 else round(100 * weighted_points / total_weight, 1)
    gaps = [
        {"dimension": item["id"], "node": gap["id"]}
        for item in dimensions
        for gap in item["gaps"]
    ]
    return {
        "project": graph.project.get("id"),
        "score": overall,
        "band": _score_band(overall),
        "applicable_weight": total_weight,
        "summary": {
            "dimensions": len(dimensions),
            "applicable_dimensions": len(applicable),
            "gaps": len(gaps),
        },
        "dimensions": dimensions,
        "gaps": gaps,
    }


def render_scorecard_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Transformation governance scorecard",
        "",
        f"- Project: `{report.get('project')}`",
        f"- Score: **{report['score']} / 100**",
        f"- Band: **{report['band']}**",
        f"- Gaps: **{report['summary']['gaps']}**",
        "",
        "| Dimension | Coverage | Weight | Weighted points | Gaps |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in report["dimensions"]:
        coverage = "N/A" if not item["applicable"] else f"{item['percentage']}% ({item['numerator']}/{item['denominator']})"
        points = "N/A" if item["weighted_points"] is None else str(item["weighted_points"])
        lines.append(f"| {item['label']} | {coverage} | {item['weight']} | {points} | {len(item['gaps'])} |")
    lines += ["", "## Gaps", ""]
    if report["gaps"]:
        for gap in report["gaps"]:
            lines.append(f"- `{gap['node']}` — {gap['dimension']}")
    else:
        lines.append("No scorecard gaps detected.")
    lines += ["", "The score is a weighted summary of the explicit dimensions above; every numerator, denominator, path, and gap remains available in the JSON report."]
    return "\n".join(lines) + "\n"


def render_scorecard_report(report: dict[str, Any], format: ScorecardFormat) -> str:
    if format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if format == "markdown":
        return render_scorecard_markdown(report)
    raise GraphValidationError(f"unsupported scorecard format: {format}")


def write_scorecard_report(report: dict[str, Any], output_path: str | Path, format: ScorecardFormat) -> None:
    Path(output_path).write_text(render_scorecard_report(report, format), encoding="utf-8")
