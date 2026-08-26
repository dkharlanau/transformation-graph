from __future__ import annotations

import argparse
import json
import sys

from .agent_context import build_context_pack, write_context_pack
from .diffing import diff_with_impact, graph_diff
from .html_export import write_html
from .importers import graph_from_csv, write_graph
from .model import Graph, GraphValidationError


def _json(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="transformation-graph", description="Validate, compose, compare, visualize, and query Git-native enterprise transformation graphs.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate a YAML or JSON graph."); validate.add_argument("file")
    stats = sub.add_parser("stats", help="Show graph statistics."); stats.add_argument("file")
    path = sub.add_parser("path", help="Find the shortest dependency path."); path.add_argument("file"); path.add_argument("source"); path.add_argument("target"); path.add_argument("--undirected", action="store_true")
    context = sub.add_parser("context", help="Emit bounded context around a node."); context.add_argument("file"); context.add_argument("node"); context.add_argument("--depth", type=int, default=1)
    context_pack = sub.add_parser("context-pack", help="Emit a stable agent-ready bounded context packet."); context_pack.add_argument("file"); context_pack.add_argument("node"); context_pack.add_argument("--depth", type=int, default=1); context_pack.add_argument("--output")
    impact = sub.add_parser("impact", help="Traverse impacted nodes around a root."); impact.add_argument("file"); impact.add_argument("node"); impact.add_argument("--depth", type=int, default=2); impact.add_argument("--direction", choices=["in", "out", "both"], default="both"); impact.add_argument("--relation", action="append", dest="relations")
    quality = sub.add_parser("quality", help="Run opinionated graph quality checks."); quality.add_argument("file"); quality.add_argument("--strict", action="store_true")
    mermaid = sub.add_parser("mermaid", help="Export graph or focused subgraph as Mermaid."); mermaid.add_argument("file"); mermaid.add_argument("--focus"); mermaid.add_argument("--depth", type=int, default=1)
    html = sub.add_parser("html", help="Generate a dependency-free single-file HTML explorer."); html.add_argument("file"); html.add_argument("--output", required=True); html.add_argument("--title")
    import_csv = sub.add_parser("import-csv", help="Build a graph from node and edge CSV files."); import_csv.add_argument("--nodes", required=True); import_csv.add_argument("--edges", required=True); import_csv.add_argument("--project-id", required=True); import_csv.add_argument("--project-name", required=True); import_csv.add_argument("--description"); import_csv.add_argument("--output", required=True)
    compose = sub.add_parser("compose", help="Compose multiple graph slices deterministically."); compose.add_argument("files", nargs="+"); compose.add_argument("--project-id", required=True); compose.add_argument("--project-name", required=True); compose.add_argument("--description"); compose.add_argument("--output", required=True)
    diff = sub.add_parser("diff", help="Compare two graph snapshots and optionally calculate neighboring impact."); diff.add_argument("before"); diff.add_argument("after"); diff.add_argument("--impact-depth", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "import-csv":
            graph = graph_from_csv(args.nodes, args.edges, args.project_id, args.project_name, args.description); write_graph(graph, args.output); _json({"written": args.output, **graph.stats()}); return 0
        if args.command == "compose":
            graphs = [Graph.from_file(path) for path in args.files]; graph = Graph.compose(graphs, args.project_id, args.project_name, args.description); write_graph(graph, args.output); _json({"written": args.output, "sources": len(graphs), **graph.stats()}); return 0
        if args.command == "diff":
            before = Graph.from_file(args.before); after = Graph.from_file(args.after); report = diff_with_impact(before, after, args.impact_depth) if args.impact_depth > 0 else graph_diff(before, after); _json(report); return 0

        graph = Graph.from_file(args.file)
        if args.command == "validate": _json({"valid": True, **graph.stats()}); return 0
        if args.command == "stats": _json(graph.stats()); return 0
        if args.command == "path":
            result = graph.path(args.source, args.target, undirected=args.undirected)
            if result is None: _json({"found": False, "source": args.source, "target": args.target, "path": []}); return 2
            _json({"found": True, "source": args.source, "target": args.target, "path": result}); return 0
        if args.command == "context": _json(graph.context(args.node, args.depth)); return 0
        if args.command == "context-pack":
            pack = build_context_pack(graph, args.node, args.depth, source=args.file)
            if args.output: write_context_pack(pack, args.output); _json({"written": args.output, "root": args.node, "depth": args.depth})
            else: _json(pack)
            return 0
        if args.command == "impact": _json(graph.impact(args.node, args.depth, args.direction, set(args.relations) if args.relations else None)); return 0
        if args.command == "quality":
            report = graph.quality(); _json(report); return 3 if args.strict and not report["passed"] else 0
        if args.command == "mermaid": print(graph.mermaid(args.focus, args.depth), end=""); return 0
        if args.command == "html": write_html(graph, args.output, args.title); _json({"written": args.output, **graph.stats()}); return 0
    except (OSError, GraphValidationError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
