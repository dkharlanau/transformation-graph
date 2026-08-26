from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import yaml

from .model import Graph, GraphValidationError

SEVERITY_ORDER = {"info": 0, "warning": 1, "error": 2}
SUPPORTED_RULE_KINDS = {"forbid_orphan", "require_attribute", "require_relation"}


def load_policy_pack(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise GraphValidationError(f"{source}: policy pack must be an object")
    if str(raw.get("version", "")) != "0.1":
        raise GraphValidationError(f"{source}: policy version must be '0.1'")
    policy = raw.get("policy")
    if not isinstance(policy, dict):
        raise GraphValidationError(f"{source}: top-level 'policy' object is required")
    if not policy.get("id") or not policy.get("name"):
        raise GraphValidationError(f"{source}: policy.id and policy.name are required")
    rules = policy.get("rules")
    if not isinstance(rules, list):
        raise GraphValidationError(f"{source}: policy.rules must be a list")
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise GraphValidationError(f"{source}: policy.rules[{index}] must be an object")
        rule_id = rule.get("id")
        kind = rule.get("kind")
        severity = rule.get("severity", "warning")
        if not isinstance(rule_id, str) or not rule_id:
            raise GraphValidationError(f"{source}: policy.rules[{index}].id is required")
        if rule_id in seen:
            raise GraphValidationError(f"{source}: duplicate policy rule id '{rule_id}'")
        seen.add(rule_id)
        if kind not in SUPPORTED_RULE_KINDS:
            raise GraphValidationError(f"{source}: policy rule '{rule_id}' has unsupported kind '{kind}'")
        if severity not in SEVERITY_ORDER:
            raise GraphValidationError(f"{source}: policy rule '{rule_id}' severity must be info, warning, or error")
        node_type = rule.get("node_type", "*")
        if not isinstance(node_type, (str, list)):
            raise GraphValidationError(f"{source}: policy rule '{rule_id}' node_type must be a string or list")
        if isinstance(node_type, list) and any(not isinstance(item, str) for item in node_type):
            raise GraphValidationError(f"{source}: policy rule '{rule_id}' node_type list must contain strings")
        if kind == "require_attribute" and not isinstance(rule.get("attribute"), str):
            raise GraphValidationError(f"{source}: require_attribute rule '{rule_id}' requires attribute")
        if kind == "require_relation":
            direction = rule.get("direction", "out")
            if direction not in {"in", "out", "both"}:
                raise GraphValidationError(f"{source}: rule '{rule_id}' direction must be in, out, or both")
            relations = rule.get("relations", rule.get("relation"))
            if isinstance(relations, str):
                relations = [relations]
            if not isinstance(relations, list) or not relations or any(not isinstance(item, str) for item in relations):
                raise GraphValidationError(f"{source}: rule '{rule_id}' requires relation or relations")
            min_count = rule.get("min_count", 1)
            if not isinstance(min_count, int) or min_count < 1:
                raise GraphValidationError(f"{source}: rule '{rule_id}' min_count must be an integer >= 1")
    return raw


def _matches_type(node_type: str, selector: str | list[str] | None) -> bool:
    if selector is None or selector == "*":
        return True
    if isinstance(selector, str):
        return node_type == selector
    return node_type in selector


def _lookup_attribute(attributes: dict[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = attributes
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _message(rule: dict[str, Any], fallback: str) -> str:
    value = rule.get("message")
    return value if isinstance(value, str) and value else fallback


def evaluate_policy_pack(graph: Graph, pack: dict[str, Any]) -> dict[str, Any]:
    policy = pack["policy"]
    findings: list[dict[str, Any]] = []
    incident: dict[str, int] = {node_id: 0 for node_id in graph.nodes}
    for edge in graph.edges:
        incident[edge.source] += 1
        incident[edge.target] += 1

    for rule in policy["rules"]:
        rule_id = rule["id"]
        kind = rule["kind"]
        severity = rule.get("severity", "warning")
        selector = rule.get("node_type", "*")
        for node_id in sorted(graph.nodes):
            node = graph.nodes[node_id]
            if not _matches_type(node.type, selector):
                continue
            if kind == "forbid_orphan":
                if incident[node_id] == 0:
                    findings.append({"policy": policy["id"], "rule": rule_id, "severity": severity, "node": node_id, "message": _message(rule, "node must participate in at least one relationship")})
                continue
            if kind == "require_attribute":
                attribute = rule["attribute"]
                exists, value = _lookup_attribute(node.attributes, attribute)
                nonempty = rule.get("nonempty", True)
                if not exists or (nonempty and (value is None or value == "")):
                    findings.append({"policy": policy["id"], "rule": rule_id, "severity": severity, "node": node_id, "message": _message(rule, f"required attribute '{attribute}' is missing")})
                continue
            if kind == "require_relation":
                relations = rule.get("relations", rule.get("relation"))
                if isinstance(relations, str):
                    relations = [relations]
                direction = rule.get("direction", "out")
                counterpart_type = rule.get("target_type")
                min_count = rule.get("min_count", 1)
                count = 0
                for edge in graph.edges:
                    counterpart = None
                    if direction in {"out", "both"} and edge.source == node_id and edge.type in relations:
                        counterpart = graph.nodes.get(edge.target)
                    if direction in {"in", "both"} and edge.target == node_id and edge.type in relations:
                        counterpart = graph.nodes.get(edge.source)
                    if counterpart is None:
                        continue
                    if counterpart_type and not _matches_type(counterpart.type, counterpart_type):
                        continue
                    count += 1
                if count < min_count:
                    relation_text = ", ".join(relations)
                    suffix = f" to {counterpart_type}" if counterpart_type else ""
                    findings.append({"policy": policy["id"], "rule": rule_id, "severity": severity, "node": node_id, "message": _message(rule, f"requires at least {min_count} {direction} relation(s) [{relation_text}]{suffix}")})

    findings.sort(key=lambda item: (-SEVERITY_ORDER[item["severity"]], item["policy"], item["rule"], item["node"]))
    summary = {
        "errors": sum(item["severity"] == "error" for item in findings),
        "warnings": sum(item["severity"] == "warning" for item in findings),
        "info": sum(item["severity"] == "info" for item in findings),
        "findings": len(findings),
    }
    return {"policy": {"id": policy["id"], "name": policy["name"]}, "passed": summary["errors"] == 0 and summary["warnings"] == 0, "summary": summary, "findings": findings}


def evaluate_policy_files(graph: Graph, paths: Iterable[str | Path]) -> dict[str, Any]:
    reports = [evaluate_policy_pack(graph, load_policy_pack(path)) for path in paths]
    findings = [item for report in reports for item in report["findings"]]
    findings.sort(key=lambda item: (-SEVERITY_ORDER[item["severity"]], item["policy"], item["rule"], item["node"]))
    summary = {
        "errors": sum(item["severity"] == "error" for item in findings),
        "warnings": sum(item["severity"] == "warning" for item in findings),
        "info": sum(item["severity"] == "info" for item in findings),
        "findings": len(findings),
    }
    return {"policies": [report["policy"] for report in reports], "passed": summary["errors"] == 0 and summary["warnings"] == 0, "summary": summary, "findings": findings}


def should_fail(report: dict[str, Any], threshold: str) -> bool:
    if threshold == "never":
        return False
    if threshold == "error":
        return report["summary"]["errors"] > 0
    if threshold == "warning":
        return report["summary"]["errors"] > 0 or report["summary"]["warnings"] > 0
    raise GraphValidationError("fail threshold must be one of: error, warning, never")
