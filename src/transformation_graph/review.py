from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable
import json

from .diffing import diff_with_impact
from .model import Graph
from .policy import evaluate_policy_files

HIGH_ATTENTION_TYPES = {"system", "interface", "mapping", "rule", "field", "change", "decision"}
MEDIUM_ATTENTION_TYPES = {"process", "process_step", "business_object", "data_object", "requirement"}


def _attention(node_type: str) -> str:
    if node_type in HIGH_ATTENTION_TYPES:
        return "high"
    if node_type in MEDIUM_ATTENTION_TYPES:
        return "medium"
    return "low"


def _changed_node_inventory(diff: dict[str, Any]) -> list[dict[str, str]]:
    inventory: dict[str, dict[str, str]] = {}
    for node in diff["nodes"]["added"]:
        inventory[node["id"]] = {"id": node["id"], "type": node["type"], "title": node["title"], "change": "added", "attention": _attention(node["type"])}
    for node in diff["nodes"]["removed"]:
        inventory[node["id"]] = {"id": node["id"], "type": node["type"], "title": node["title"], "change": "removed", "attention": _attention(node["type"])}
    for item in diff["nodes"]["changed"]:
        node = item["after"]
        inventory[node["id"]] = {"id": node["id"], "type": node["type"], "title": node["title"], "change": "changed", "attention": _attention(node["type"])}
    return sorted(inventory.values(), key=lambda item: ({"high": 0, "medium": 1, "low": 2}[item["attention"]], item["type"], item["id"]))


def _new_findings(before: dict[str, Any], after: dict[str, Any], identity_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    def key(item: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(item.get(field) for field in identity_keys)
    before_keys = {key(item) for item in before.get("findings", [])}
    return [item for item in after.get("findings", []) if key(item) not in before_keys]


def build_review_report(before: Graph, after: Graph, impact_depth: int = 1, policy_paths: Iterable[str | Path] = ()) -> dict[str, Any]:
    diff = diff_with_impact(before, after, depth=impact_depth)
    changed_nodes = _changed_node_inventory(diff)
    attention = Counter(item["attention"] for item in changed_nodes)
    impact_by_type = Counter(item["type"] for item in diff["impact"]["impacted_nodes"])
    quality_before = before.quality()
    quality_after = after.quality()
    quality_new = _new_findings(quality_before, quality_after, ("code", "severity", "node", "message"))
    policy_paths = list(policy_paths)
    policies: dict[str, Any] | None = None
    if policy_paths:
        policy_before = evaluate_policy_files(before, policy_paths)
        policy_after = evaluate_policy_files(after, policy_paths)
        policies = {"before": policy_before, "after": policy_after, "new_findings": _new_findings(policy_before, policy_after, ("policy", "rule", "severity", "node", "message"))}
    return {
        "format_version": "0.1",
        "before_project": before.project.get("id"),
        "after_project": after.project.get("id"),
        "impact_depth": impact_depth,
        "change_summary": diff["summary"],
        "changed_roots": diff["changed_roots"],
        "changed_nodes": changed_nodes,
        "attention_summary": {"high": attention["high"], "medium": attention["medium"], "low": attention["low"]},
        "impact": {"nodes": diff["impact"]["impacted_nodes"], "by_type": dict(sorted(impact_by_type.items()))},
        "quality": {"before": quality_before, "after": quality_after, "new_findings": quality_new},
        "policies": policies,
        "diff": diff,
    }


def _escape_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown_report(report: dict[str, Any]) -> str:
    summary = report["change_summary"]
    lines = ["# Transformation Graph change review", "", f"**Project:** `{report['before_project']}` → `{report['after_project']}`", f"**Impact depth:** {report['impact_depth']}", "", "## Change summary", "", "| Change | Count |", "| --- | ---: |"]
    labels = (("Nodes added", "nodes_added"), ("Nodes removed", "nodes_removed"), ("Nodes changed", "nodes_changed"), ("Edges added", "edges_added"), ("Edges removed", "edges_removed"), ("Edges changed", "edges_changed"))
    for label, key in labels:
        lines.append(f"| {label} | {summary[key]} |")
    lines.extend(["", "## Review attention", ""])
    attention = report["attention_summary"]
    lines.append(f"High: **{attention['high']}** · Medium: **{attention['medium']}** · Low: **{attention['low']}**")
    if report["changed_nodes"]:
        lines.extend(["", "| Attention | Change | Type | Node |", "| --- | --- | --- | --- |"])
        for item in report["changed_nodes"]:
            lines.append("| {attention} | {change} | `{type}` | `{id}` — {title} |".format(attention=_escape_cell(item["attention"]), change=_escape_cell(item["change"]), type=_escape_cell(item["type"]), id=_escape_cell(item["id"]), title=_escape_cell(item["title"])))
    else:
        lines.append("No node-level changes.")
    lines.extend(["", "## Neighboring impact", ""])
    impacted = report["impact"]["nodes"]
    if impacted:
        lines.extend(["| Type | Node |", "| --- | --- |"])
        for node in impacted:
            lines.append(f"| `{_escape_cell(node['type'])}` | `{_escape_cell(node['id'])}` — {_escape_cell(node['title'])} |")
    else:
        lines.append("No neighboring nodes found at the configured depth.")
    lines.extend(["", "## Quality delta", ""])
    before_summary = report["quality"]["before"]["summary"]
    after_summary = report["quality"]["after"]["summary"]
    lines.append(f"Built-in findings: **{before_summary['findings']} → {after_summary['findings']}** (new: **{len(report['quality']['new_findings'])}**).")
    for finding in report["quality"]["new_findings"]:
        lines.append(f"- **{finding['severity']}** `{finding['code']}` on `{finding['node']}` — {finding['message']}")
    policies = report.get("policies")
    if policies is not None:
        lines.extend(["", "## Policy delta", ""])
        before = policies["before"]["summary"]
        after = policies["after"]["summary"]
        lines.append(f"Policy findings: **{before['findings']} → {after['findings']}** (new: **{len(policies['new_findings'])}**).")
        for finding in policies["new_findings"]:
            lines.append(f"- **{finding['severity']}** `{finding['policy']}/{finding['rule']}` on `{finding['node']}` — {finding['message']}")
    lines.extend(["", "> Review attention is a deterministic triage signal based on changed node types, not a business-risk score.", ""])
    return "\n".join(lines)


def write_review_report(report: dict[str, Any], output_path: str | Path, format: str = "markdown") -> None:
    path = Path(output_path)
    if format == "markdown":
        path.write_text(render_markdown_report(report), encoding="utf-8")
        return
    if format == "json":
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        return
    raise ValueError("review format must be markdown or json")
