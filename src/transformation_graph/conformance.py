from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from .adapters import AdapterKind
from .model import Edge, Graph, GraphValidationError

ConformanceFormat = Literal["json", "markdown"]


def _finding(code: str, severity: str, message: str, node: str | None = None) -> dict[str, str]:
    item = {"code": code, "severity": severity, "message": message}
    if node:
        item["node"] = node
    return item


def _outgoing(graph: Graph, node_id: str, relation: str | None = None) -> list[Edge]:
    return sorted(
        [edge for edge in graph.edges if edge.source == node_id and (relation is None or edge.type == relation)],
        key=lambda edge: (edge.type, edge.target, edge.label or ""),
    )


def _incoming(graph: Graph, node_id: str, relation: str | None = None) -> list[Edge]:
    return sorted(
        [edge for edge in graph.edges if edge.target == node_id and (relation is None or edge.type == relation)],
        key=lambda edge: (edge.type, edge.source, edge.label or ""),
    )


def _targets_of_type(graph: Graph, edges: list[Edge], node_type: str) -> list[str]:
    return [edge.target for edge in edges if edge.target in graph.nodes and graph.nodes[edge.target].type == node_type]


def _sources_of_type(graph: Graph, edges: list[Edge], node_type: str) -> list[str]:
    return [edge.source for edge in edges if edge.source in graph.nodes and graph.nodes[edge.source].type == node_type]


def _mapping_conformance(graph: Graph, findings: list[dict[str, str]]) -> None:
    mappings = sorted(node.id for node in graph.nodes.values() if node.type == "mapping")
    if not mappings:
        findings.append(_finding("MAPPING_NODE_MISSING", "error", "adapter output contains no mapping node"))
        return
    for mapping_id in mappings:
        source_objects = _targets_of_type(graph, _outgoing(graph, mapping_id, "maps_from"), "data_object")
        target_objects = _targets_of_type(graph, _outgoing(graph, mapping_id, "maps_to"), "data_object")
        if not source_objects:
            findings.append(_finding("MAPPING_SOURCE_MISSING", "error", "mapping has no maps_from data object", mapping_id))
        if not target_objects:
            findings.append(_finding("MAPPING_TARGET_MISSING", "error", "mapping has no maps_to data object", mapping_id))
        rules = _targets_of_type(graph, _outgoing(graph, mapping_id, "contains_rule"), "rule")
        if not rules:
            findings.append(_finding("MAPPING_FIELD_RULES_MISSING", "warning", "mapping contains no field-level rules", mapping_id))
        for rule_id in rules:
            reads = _targets_of_type(graph, _outgoing(graph, rule_id, "reads"), "field")
            writes = _targets_of_type(graph, _outgoing(graph, rule_id, "writes"), "field")
            if not reads:
                findings.append(_finding("RULE_SOURCE_FIELD_MISSING", "error", "field rule reads no source field", rule_id))
            if not writes:
                findings.append(_finding("RULE_TARGET_FIELD_MISSING", "error", "field rule writes no target field", rule_id))


def _interface_conformance(graph: Graph, findings: list[dict[str, str]]) -> None:
    interfaces = sorted(node.id for node in graph.nodes.values() if node.type == "interface")
    if not interfaces:
        findings.append(_finding("INTERFACE_NODE_MISSING", "error", "adapter output contains no interface node"))
        return
    for interface_id in interfaces:
        sources = _targets_of_type(graph, _outgoing(graph, interface_id, "sourced_from"), "system")
        targets = _targets_of_type(graph, _outgoing(graph, interface_id, "delivers_to"), "system")
        owners = _targets_of_type(graph, _outgoing(graph, interface_id, "owned_by"), "owner")
        tests = _sources_of_type(graph, _incoming(graph, interface_id, "validates"), "test")
        if not sources:
            findings.append(_finding("INTERFACE_SOURCE_SYSTEM_MISSING", "error", "interface has no source system", interface_id))
        if not targets:
            findings.append(_finding("INTERFACE_TARGET_SYSTEM_MISSING", "error", "interface has no target system", interface_id))
        if not owners:
            findings.append(_finding("INTERFACE_OWNER_MISSING", "warning", "interface has no ownership relationship", interface_id))
        if not tests:
            findings.append(_finding("INTERFACE_TEST_MISSING", "warning", "interface has no validating test", interface_id))


def _reachable_steps(graph: Graph, start: str, step_ids: set[str]) -> set[str]:
    seen = {start}
    frontier = [start]
    while frontier:
        current = frontier.pop(0)
        for edge in _outgoing(graph, current, "precedes"):
            if edge.target in step_ids and edge.target not in seen:
                seen.add(edge.target)
                frontier.append(edge.target)
    return seen


def _process_conformance(graph: Graph, findings: list[dict[str, str]]) -> None:
    processes = sorted(node.id for node in graph.nodes.values() if node.type == "process")
    if not processes:
        findings.append(_finding("PROCESS_NODE_MISSING", "error", "adapter output contains no process node"))
        return
    for process_id in processes:
        step_ids = set(_targets_of_type(graph, _outgoing(graph, process_id, "contains"), "process_step"))
        if not step_ids:
            findings.append(_finding("PROCESS_STEPS_MISSING", "error", "process contains no steps", process_id))
            continue
        if not _targets_of_type(graph, _outgoing(graph, process_id, "owned_by"), "owner"):
            findings.append(_finding("PROCESS_OWNER_MISSING", "warning", "process has no owner", process_id))
        start_key = graph.nodes[process_id].attributes.get("start")
        if not start_key:
            findings.append(_finding("PROCESS_START_MISSING", "warning", "process does not declare a start step", process_id))
        else:
            suffix = f".{start_key}"
            candidates = sorted(step_id for step_id in step_ids if step_id.endswith(suffix))
            if not candidates:
                findings.append(_finding("PROCESS_START_UNKNOWN", "error", f"declared start step '{start_key}' was not normalized", process_id))
            else:
                reachable = _reachable_steps(graph, candidates[0], step_ids)
                for step_id in sorted(step_ids - reachable):
                    findings.append(_finding("PROCESS_STEP_UNREACHABLE", "warning", "process step is not reachable from the declared start", step_id))
        for step_id in sorted(step_ids):
            step_kind = graph.nodes[step_id].attributes.get("type")
            if step_kind == "user_task" and not _targets_of_type(graph, _outgoing(graph, step_id, "performed_by"), "owner"):
                findings.append(_finding("USER_TASK_ACTOR_MISSING", "warning", "user task has no normalized actor", step_id))
            if step_kind == "service_task":
                has_system = bool(_targets_of_type(graph, _outgoing(graph, step_id, "runs_in"), "system"))
                has_interface = bool(_targets_of_type(graph, _outgoing(graph, step_id, "uses_interface"), "interface"))
                if not has_system and not has_interface:
                    findings.append(_finding("SERVICE_TASK_EXECUTION_MISSING", "warning", "service task has neither a system nor an interface", step_id))


def evaluate_adapter_graph(graph: Graph, kind: AdapterKind) -> dict[str, Any]:
    """Evaluate semantic conformance of a graph produced by an as-code adapter."""
    findings: list[dict[str, str]] = []
    expected_format = f"{kind}-as-code"
    if graph.project.get("source_format") != expected_format:
        findings.append(
            _finding(
                "ADAPTER_SOURCE_FORMAT_MISMATCH",
                "warning",
                f"project.source_format is '{graph.project.get('source_format')}', expected '{expected_format}'",
            )
        )
    if kind == "mapping":
        _mapping_conformance(graph, findings)
    elif kind == "interface":
        _interface_conformance(graph, findings)
    elif kind == "process":
        _process_conformance(graph, findings)
    else:
        raise GraphValidationError(f"unsupported adapter kind: {kind}")
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    return {
        "adapter": kind,
        "project": graph.project.get("id"),
        "passed": errors == 0,
        "summary": {"errors": errors, "warnings": warnings, "findings": len(findings)},
        "findings": findings,
        "stats": graph.stats(),
    }


def should_fail_conformance(report: dict[str, Any], threshold: str) -> bool:
    if threshold == "never":
        return False
    if threshold == "warning":
        return bool(report["summary"]["errors"] or report["summary"]["warnings"])
    if threshold == "error":
        return bool(report["summary"]["errors"])
    raise GraphValidationError("conformance threshold must be error, warning, or never")


def render_conformance_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# {str(report['adapter']).title()} adapter conformance",
        "",
        f"- Project: `{report.get('project')}`",
        f"- Status: **{'PASS' if report['passed'] else 'FAIL'}**",
        f"- Errors: **{summary['errors']}**",
        f"- Warnings: **{summary['warnings']}**",
        "",
        "| Severity | Code | Node | Finding |",
        "| --- | --- | --- | --- |",
    ]
    for finding in report["findings"]:
        message = finding["message"].replace("|", "\\|")
        lines.append(f"| {finding['severity']} | `{finding['code']}` | `{finding.get('node', '')}` | {message} |")
    if not report["findings"]:
        lines.append("| — | — | — | No conformance findings |")
    return "\n".join(lines) + "\n"


def render_conformance_report(report: dict[str, Any], format: ConformanceFormat) -> str:
    if format == "json":
        return json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if format == "markdown":
        return render_conformance_markdown(report)
    raise GraphValidationError(f"unsupported conformance format: {format}")


def write_conformance_report(report: dict[str, Any], output_path: str | Path, format: ConformanceFormat) -> None:
    Path(output_path).write_text(render_conformance_report(report, format), encoding="utf-8")
