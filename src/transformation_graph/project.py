from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .adapters import AdapterKind
from .composition import compose_adapter_documents, compose_reconciled
from .importers import write_graph
from .model import Graph, GraphValidationError
from .policy import evaluate_policy_files, should_fail
from .scorecard import build_scorecard
from .site_export import build_site
from .site_extensions import augment_site

ADAPTER_KINDS = {"mapping", "interface", "process"}


def load_project_manifest(path: str | Path) -> tuple[Path, dict[str, Any]]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict): raise GraphValidationError(f"{source}: project manifest must be an object")
    if str(raw.get("version", "")) != "0.1": raise GraphValidationError(f"{source}: project manifest version must be '0.1'")
    project = raw.get("project")
    if not isinstance(project, dict) or not project.get("id") or not project.get("name"): raise GraphValidationError(f"{source}: project.id and project.name are required")
    sources = raw.get("sources")
    if not isinstance(sources, dict): raise GraphValidationError(f"{source}: sources must be an object")
    adapters = sources.get("adapters", []); graphs = sources.get("graphs", [])
    if not isinstance(adapters, list) or not isinstance(graphs, list): raise GraphValidationError(f"{source}: sources.adapters and sources.graphs must be lists")
    if not adapters and not graphs: raise GraphValidationError(f"{source}: at least one adapter or canonical graph source is required")
    for index, item in enumerate(adapters):
        if not isinstance(item, dict): raise GraphValidationError(f"{source}: sources.adapters[{index}] must be an object")
        if item.get("kind") not in ADAPTER_KINDS: raise GraphValidationError(f"{source}: sources.adapters[{index}].kind must be mapping, interface, or process")
        if not isinstance(item.get("path"), str) or not item["path"]: raise GraphValidationError(f"{source}: sources.adapters[{index}].path is required")
    for index, item in enumerate(graphs):
        path_value = item if isinstance(item, str) else item.get("path") if isinstance(item, dict) else None
        if not isinstance(path_value, str) or not path_value: raise GraphValidationError(f"{source}: sources.graphs[{index}] must be a path string or object with path")
    governance = raw.get("governance", {})
    if governance is not None and not isinstance(governance, dict): raise GraphValidationError(f"{source}: governance must be an object")
    publish = raw.get("publish", {})
    if publish is not None and not isinstance(publish, dict): raise GraphValidationError(f"{source}: publish must be an object")
    return source, raw


def _resolve(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _empty_policy_report() -> dict[str, Any]:
    return {"policies": [], "passed": True, "summary": {"errors": 0, "warnings": 0, "info": 0, "findings": 0}, "findings": []}


def build_project(manifest_path: str | Path, output_dir: str | Path, *, base_url_override: str | None = None, force_site: bool | None = None) -> dict[str, Any]:
    """Build one governed transformation graph and its outputs from a declarative project manifest."""
    source, manifest = load_project_manifest(manifest_path); base = source.parent
    project = manifest["project"]; sources = manifest["sources"]; governance = manifest.get("governance") or {}; publish = manifest.get("publish") or {}
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)

    conformance_fail_on = str(governance.get("conformance_fail_on", "error"))
    if conformance_fail_on not in {"error", "warning", "never"}: raise GraphValidationError("governance.conformance_fail_on must be error, warning, or never")
    adapter_specs: list[tuple[AdapterKind, Path]] = [(item["kind"], _resolve(base, item["path"])) for item in sources.get("adapters", [])]

    build_graphs: list[Graph] = []; conformance: list[dict[str, Any]] = []
    if adapter_specs:
        adapter_graph, conformance = compose_adapter_documents(adapter_specs, f"{project['id']}-adapters", f"{project['name']} adapters", project.get("description"), fail_on=conformance_fail_on)
        build_graphs.append(adapter_graph)
    graph_paths: list[Path] = []
    for item in sources.get("graphs", []):
        path_value = item if isinstance(item, str) else item["path"]
        resolved = _resolve(base, path_value); graph_paths.append(resolved); build_graphs.append(Graph.from_file(resolved))

    graph = compose_reconciled(build_graphs, str(project["id"]), str(project["name"]), project.get("description"))
    graph_path = output / "graph.yaml"; write_graph(graph, graph_path)

    raw_policy_paths = governance.get("policies", [])
    if not isinstance(raw_policy_paths, list) or any(not isinstance(value, str) for value in raw_policy_paths): raise GraphValidationError("governance.policies must be a list of paths")
    policy_paths = [_resolve(base, value) for value in raw_policy_paths]
    policy_report = evaluate_policy_files(graph, policy_paths) if policy_paths else _empty_policy_report()
    policy_fail_on = str(governance.get("policy_fail_on", "error"))
    if policy_fail_on not in {"error", "warning", "never"}: raise GraphValidationError("governance.policy_fail_on must be error, warning, or never")
    policy_failed = should_fail(policy_report, policy_fail_on)

    scorecard = build_scorecard(graph); score_threshold = governance.get("score_fail_below")
    if score_threshold is not None:
        if not isinstance(score_threshold, (int, float)) or isinstance(score_threshold, bool): raise GraphValidationError("governance.score_fail_below must be a number")
        if not 0 <= float(score_threshold) <= 100: raise GraphValidationError("governance.score_fail_below must be between 0 and 100")
    score_failed = score_threshold is not None and scorecard["score"] < float(score_threshold)

    (output / "conformance.json").write_text(json.dumps(conformance, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (output / "policy.json").write_text(json.dumps(policy_report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (output / "scorecard.json").write_text(json.dumps(scorecard, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

    site_enabled = bool(publish.get("site", False)) if force_site is None else force_site; site_manifest = None
    if site_enabled:
        base_url = base_url_override if base_url_override is not None else publish.get("base_url")
        site_manifest = build_site(graph, output / "site", title=publish.get("title"), base_url=base_url)
        site_manifest = augment_site(graph, output / "site", site_manifest)

    report: dict[str, Any] = {
        "format": "transformation-graph-project-build", "version": "0.1", "manifest": str(source), "project": dict(project),
        "sources": {"adapters": [{"kind": kind, "path": str(path)} for kind, path in adapter_specs], "graphs": [str(path) for path in graph_paths]},
        "graph": graph.stats(), "conformance": conformance,
        "governance": {"policy_fail_on": policy_fail_on, "policy": policy_report, "score_fail_below": score_threshold, "scorecard": scorecard},
        "outputs": {"graph": str(graph_path), "conformance": str(output / "conformance.json"), "policy": str(output / "policy.json"), "scorecard": str(output / "scorecard.json"), **({"site": str(output / "site")} if site_enabled else {})},
        "site_manifest": site_manifest, "passed": not policy_failed and not score_failed, "failures": {"policy": policy_failed, "score": score_failed},
    }
    (output / "build-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return report
