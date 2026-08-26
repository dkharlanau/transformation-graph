from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .model import Graph

CONTEXT_PACK_FORMAT = "transformation-graph/context-pack"
CONTEXT_PACK_VERSION = "0.1"


def build_context_pack(graph: Graph, root: str, depth: int = 1, source: str | None = None) -> dict[str, Any]:
    """Build a deterministic, bounded context packet for agent consumption."""
    context = graph.context(root, depth=depth)
    selected_ids = {node["id"] for node in context["nodes"]}
    quality = graph.quality()
    relevant_findings = [
        finding for finding in quality["findings"] if finding.get("node") in selected_ids
    ]

    pack: dict[str, Any] = {
        "format": CONTEXT_PACK_FORMAT,
        "version": CONTEXT_PACK_VERSION,
        "project": dict(graph.project),
        "query": {"root": root, "depth": depth},
        "root": graph.nodes[root].as_dict(),
        "graph_stats": graph.stats(),
        "context": {"nodes": context["nodes"], "edges": context["edges"]},
        "quality_findings": relevant_findings,
        "provenance": {},
    }
    if source:
        pack["provenance"]["source"] = source
    return pack


def write_context_pack(pack: dict[str, Any], output_path: str | Path) -> None:
    Path(output_path).write_text(
        json.dumps(pack, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
