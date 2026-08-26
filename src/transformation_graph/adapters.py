from __future__ import annotations

from pathlib import Path
from typing import Any, Literal
import json
import re

import yaml

from .model import Graph, GraphValidationError

AdapterKind = Literal["mapping", "interface", "process"]


def _load_document(path: str | Path) -> tuple[Path, dict[str, Any]]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        if source.suffix.lower() in {".yaml", ".yml"}:
            raw = yaml.safe_load(handle)
        elif source.suffix.lower() == ".json":
            raw = json.load(handle)
        else:
            raise GraphValidationError("adapter input must be YAML (.yaml/.yml) or JSON (.json)")
    if not isinstance(raw, dict):
        raise GraphValidationError("adapter input must contain a top-level object")
    return source, raw


def _slug(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "unknown"
    text = re.sub(r"[^A-Za-z0-9_.:-]+", "-", text)
    return text.strip("-") or "unknown"


def _id(kind: str, value: Any) -> str:
    return f"{kind}.{_slug(value)}"


class _Builder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[tuple[str, str, str, str | None], dict[str, Any]] = {}

    def node(
        self,
        node_id: str,
        node_type: str,
        title: Any,
        *,
        description: str | None = None,
        tags: list[str] | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> str:
        candidate: dict[str, Any] = {"id": node_id, "type": node_type, "title": str(title)}
        if description:
            candidate["description"] = description
        if tags:
            candidate["tags"] = [str(item) for item in tags]
        if attributes:
            candidate["attributes"] = attributes
        existing = self.nodes.get(node_id)
        if existing is None:
            self.nodes[node_id] = candidate
        elif existing["type"] != node_type:
            raise GraphValidationError(f"adapter generated conflicting node type for '{node_id}'")
        return node_id

    def edge(
        self,
        source: str,
        target: str,
        relation: str,
        *,
        label: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        key = (source, target, relation, label)
        if key in self.edges:
            return
        edge: dict[str, Any] = {"from": source, "to": target, "type": relation}
        if label:
            edge["label"] = label
        if attributes:
            edge["attributes"] = attributes
        self.edges[key] = edge

    def graph(
        self,
        project_id: str,
        project_name: str,
        source_format: str,
        source_file: str,
        description: str | None = None,
    ) -> Graph:
        project: dict[str, Any] = {
            "id": project_id,
            "name": project_name,
            "source_format": source_format,
            "source_file": source_file,
        }
        if description:
            project["description"] = description
        return Graph(
            {
                "version": "0.1",
                "project": project,
                "nodes": [self.nodes[node_id] for node_id in sorted(self.nodes)],
                "edges": sorted(
                    self.edges.values(),
                    key=lambda item: (item["from"], item["to"], item["type"], item.get("label", "")),
                ),
            }
        )


def graph_from_mapping_as_code(
    path: str | Path,
    project_id: str | None = None,
    project_name: str | None = None,
) -> Graph:
    source, raw = _load_document(path)
    mapping = raw.get("mapping")
    if not isinstance(mapping, dict):
        raise GraphValidationError("mapping adapter expects a top-level 'mapping' object")
    mapping_id = mapping.get("id")
    if not mapping_id:
        raise GraphValidationError("mapping.id is required")

    builder = _Builder()
    mapping_node = builder.node(
        _id("mapping", mapping_id),
        "mapping",
        mapping.get("name") or mapping_id,
        description=mapping.get("description"),
        attributes={
            key: value
            for key, value in mapping.items()
            if key not in {"id", "name", "description", "fields"} and value is not None
        },
    )

    source_endpoint = mapping.get("source")
    target_endpoint = mapping.get("target")
    source_object = None
    target_object = None
    if source_endpoint:
        source_object = builder.node(
            _id("data_object", source_endpoint),
            "data_object",
            source_endpoint,
            attributes={"role": "source"},
        )
        builder.edge(mapping_node, source_object, "maps_from")
    if target_endpoint:
        target_object = builder.node(
            _id("data_object", target_endpoint),
            "data_object",
            target_endpoint,
            attributes={"role": "target"},
        )
        builder.edge(mapping_node, target_object, "maps_to")

    fields = mapping.get("fields", [])
    if fields is None:
        fields = []
    if not isinstance(fields, list):
        raise GraphValidationError("mapping.fields must be a list")

    for index, field_mapping in enumerate(fields, start=1):
        if not isinstance(field_mapping, dict):
            raise GraphValidationError(f"mapping.fields[{index - 1}] must be an object")
        source_field = field_mapping.get("source")
        target_field = field_mapping.get("target")
        if not source_field or not target_field:
            raise GraphValidationError(f"mapping.fields[{index - 1}] requires source and target")
        rule_value = field_mapping.get("rule")
        rule_id = _id("rule", f"{mapping_id}.{index}")
        rule_node = builder.node(
            rule_id,
            "rule",
            f"{source_field} → {target_field}",
            attributes={
                "source_field": source_field,
                "target_field": target_field,
                **({"rule": rule_value} if rule_value is not None else {}),
            },
        )
        builder.edge(mapping_node, rule_node, "contains_rule")

        source_field_id = builder.node(
            _id("field", f"{source_endpoint or 'source'}.{source_field}"),
            "field",
            source_field,
            attributes={"side": "source"},
        )
        target_field_id = builder.node(
            _id("field", f"{target_endpoint or 'target'}.{target_field}"),
            "field",
            target_field,
            attributes={"side": "target"},
        )
        if source_object:
            builder.edge(source_object, source_field_id, "contains")
        if target_object:
            builder.edge(target_object, target_field_id, "contains")
        builder.edge(rule_node, source_field_id, "reads")
        builder.edge(rule_node, target_field_id, "writes")

    return builder.graph(
        project_id or f"mapping-{_slug(mapping_id)}",
        project_name or f"Mapping: {mapping.get('name') or mapping_id}",
        "mapping-as-code",
        source.name,
        mapping.get("description"),
    )


def graph_from_interface_as_code(
    path: str | Path,
    project_id: str | None = None,
    project_name: str | None = None,
) -> Graph:
    source, raw = _load_document(path)
    interface = raw.get("interface")
    if not isinstance(interface, dict):
        raise GraphValidationError("interface adapter expects a top-level 'interface' object")
    interface_id = interface.get("id")
    if not interface_id:
        raise GraphValidationError("interface.id is required")

    builder = _Builder()
    attributes = {
        key: raw[key]
        for key in (
            "trigger",
            "contract",
            "delivery",
            "retry",
            "monitoring",
            "reconciliation",
            "sla",
            "security",
            "profiles",
        )
        if key in raw
    }
    attributes.update(
        {
            key: interface[key]
            for key in ("mode", "pattern", "criticality", "lifecycle")
            if interface.get(key) is not None
        }
    )
    interface_node = builder.node(
        _id("interface", interface_id),
        "interface",
        interface.get("name") or interface_id,
        description=interface.get("description"),
        tags=interface.get("tags") if isinstance(interface.get("tags"), list) else None,
        attributes=attributes,
    )

    def system_node(value: Any, role: str) -> str | None:
        if not value:
            return None
        return builder.node(_id("system", value), "system", value, attributes={"adapter_role": role})

    source_spec = interface.get("source") if isinstance(interface.get("source"), dict) else {}
    target_spec = interface.get("target") if isinstance(interface.get("target"), dict) else {}
    source_system = system_node(source_spec.get("system"), "source")
    target_system = system_node(target_spec.get("system"), "target")
    if source_system:
        builder.edge(interface_node, source_system, "sourced_from")
    if target_system:
        builder.edge(interface_node, target_system, "delivers_to")

    for system in (raw.get("route") or {}).get("middleware", []) if isinstance(raw.get("route"), dict) else []:
        middleware = system_node(system, "middleware")
        if middleware:
            builder.edge(interface_node, middleware, "routes_via")

    if source_spec.get("object"):
        object_key = f"{source_spec.get('system') or 'source'}.{source_spec['object']}"
        object_node = builder.node(_id("data_object", object_key), "data_object", object_key)
        builder.edge(interface_node, object_node, "reads")
    if target_spec.get("object"):
        object_key = f"{target_spec.get('system') or 'target'}.{target_spec['object']}"
        object_node = builder.node(_id("data_object", object_key), "data_object", object_key)
        builder.edge(interface_node, object_node, "writes")

    ownership = raw.get("ownership")
    if isinstance(ownership, dict):
        for role, owner in ownership.items():
            if not owner:
                continue
            owner_node = builder.node(
                _id("owner", owner),
                "owner",
                owner,
                attributes={"adapter_role": role},
            )
            builder.edge(interface_node, owner_node, "owned_by", label=str(role))

    mapping = raw.get("mapping")
    if isinstance(mapping, dict):
        mapping_key = mapping.get("profile") or mapping.get("file") or f"{interface_id}-mapping"
        mapping_node = builder.node(
            _id("mapping", mapping_key),
            "mapping",
            mapping.get("profile") or mapping.get("file") or "Interface mapping",
            attributes={key: value for key, value in mapping.items() if value is not None},
        )
        builder.edge(interface_node, mapping_node, "uses_mapping")

    tests = raw.get("tests", [])
    if tests is None:
        tests = []
    if not isinstance(tests, list):
        raise GraphValidationError("tests must be a list")
    for index, test in enumerate(tests, start=1):
        if not isinstance(test, dict):
            raise GraphValidationError(f"tests[{index - 1}] must be an object")
        test_key = test.get("id") or index
        test_node = builder.node(
            _id("test", f"{interface_id}.{test_key}"),
            "test",
            test.get("description") or test.get("id") or f"Interface test {index}",
            attributes={
                key: value
                for key, value in test.items()
                if key not in {"id", "description"} and value is not None
            },
        )
        builder.edge(test_node, interface_node, "validates")

    return builder.graph(
        project_id or f"interface-{_slug(interface_id)}",
        project_name or f"Interface: {interface.get('name') or interface_id}",
        "interface-as-code",
        source.name,
        interface.get("description"),
    )


def graph_from_process_as_code(
    path: str | Path,
    project_id: str | None = None,
    project_name: str | None = None,
) -> Graph:
    source, raw = _load_document(path)
    process = raw.get("process")
    if not isinstance(process, dict):
        raise GraphValidationError("process adapter expects a top-level 'process' object")
    process_id = process.get("id")
    if not process_id:
        raise GraphValidationError("process.id is required")

    builder = _Builder()
    process_node = builder.node(
        _id("process", process_id),
        "process",
        process.get("name") or process_id,
        description=process.get("description"),
        attributes={
            key: process[key]
            for key in ("start", "trigger", "outcome")
            if process.get(key) is not None
        },
    )

    maps: dict[str, dict[str, str]] = {
        "roles": {},
        "systems": {},
        "objects": {},
        "interfaces": {},
        "controls": {},
        "risks": {},
        "evidence": {},
    }

    def register(collection: str, node_type: str, prefix: str, attributes: dict[str, Any] | None = None) -> None:
        items = raw.get(collection, [])
        if items is None:
            return
        if not isinstance(items, list):
            raise GraphValidationError(f"{collection} must be a list")
        for index, item in enumerate(items):
            if not isinstance(item, dict) or not item.get("id"):
                raise GraphValidationError(f"{collection}[{index}] requires an id")
            item_id = str(item["id"])
            node = builder.node(
                _id(prefix, item_id),
                node_type,
                item.get("name") or item_id,
                attributes={
                    **(attributes or {}),
                    **{
                        key: value
                        for key, value in item.items()
                        if key not in {"id", "name"} and value is not None
                    },
                },
            )
            maps[collection][item_id] = node

    register("roles", "owner", "owner", {"kind": "process_role"})
    register("systems", "system", "system")
    register("objects", "business_object", "business_object")
    register("interfaces", "interface", "interface")
    register("controls", "rule", "rule", {"kind": "control"})
    register("risks", "x-risk", "risk")
    register("evidence", "evidence", "evidence")

    owner = process.get("owner")
    if owner and str(owner) in maps["roles"]:
        builder.edge(process_node, maps["roles"][str(owner)], "owned_by")

    steps = raw.get("steps", [])
    if not isinstance(steps, list) or not steps:
        raise GraphValidationError("steps must be a non-empty list")

    step_nodes: dict[str, str] = {}
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or not step.get("id"):
            raise GraphValidationError(f"steps[{index}] requires an id")
        step_id = str(step["id"])
        attributes = {
            key: value
            for key, value in step.items()
            if key
            not in {
                "id",
                "name",
                "description",
                "actor",
                "system",
                "objects",
                "interfaces",
                "controls",
                "risks",
                "evidence",
                "transitions",
            }
            and value is not None
        }
        step_node = builder.node(
            _id("process_step", f"{process_id}.{step_id}"),
            "process_step",
            step.get("name") or step_id,
            description=step.get("description"),
            attributes=attributes,
        )
        step_nodes[step_id] = step_node
        builder.edge(process_node, step_node, "contains")

        for field, collection, relation in (
            ("actor", "roles", "performed_by"),
            ("system", "systems", "runs_in"),
        ):
            value = step.get(field)
            if value is not None and str(value) in maps[collection]:
                builder.edge(step_node, maps[collection][str(value)], relation)

        for field, collection, relation in (
            ("objects", "objects", "uses"),
            ("interfaces", "interfaces", "uses_interface"),
            ("controls", "controls", "controlled_by"),
            ("risks", "risks", "exposed_to"),
            ("evidence", "evidence", "evidenced_by"),
        ):
            values = step.get(field, [])
            if values is None:
                continue
            if not isinstance(values, list):
                raise GraphValidationError(f"step '{step_id}' field '{field}' must be a list")
            for value in values:
                if str(value) in maps[collection]:
                    builder.edge(step_node, maps[collection][str(value)], relation)

    for step in steps:
        step_id = str(step["id"])
        transitions = step.get("transitions", [])
        if transitions is None:
            continue
        if not isinstance(transitions, list):
            raise GraphValidationError(f"step '{step_id}' transitions must be a list")
        for index, transition in enumerate(transitions):
            if not isinstance(transition, dict) or not transition.get("to"):
                raise GraphValidationError(f"step '{step_id}' transition[{index}] requires 'to'")
            target = str(transition["to"])
            if target not in step_nodes:
                raise GraphValidationError(f"step '{step_id}' transition references unknown step '{target}'")
            builder.edge(
                step_nodes[step_id],
                step_nodes[target],
                "precedes",
                label=transition.get("label"),
                attributes={
                    key: value
                    for key, value in transition.items()
                    if key not in {"to", "label"} and value is not None
                },
            )

    return builder.graph(
        project_id or f"process-{_slug(process_id)}",
        project_name or f"Process: {process.get('name') or process_id}",
        "process-as-code",
        source.name,
        process.get("description"),
    )


def graph_from_as_code(
    path: str | Path,
    kind: AdapterKind,
    project_id: str | None = None,
    project_name: str | None = None,
) -> Graph:
    if kind == "mapping":
        return graph_from_mapping_as_code(path, project_id, project_name)
    if kind == "interface":
        return graph_from_interface_as_code(path, project_id, project_name)
    if kind == "process":
        return graph_from_process_as_code(path, project_id, project_name)
    raise GraphValidationError(f"unsupported adapter kind: {kind}")
