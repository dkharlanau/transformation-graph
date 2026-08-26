from __future__ import annotations
import argparse, json, sys
from .model import Graph, GraphValidationError
from .importers import graph_from_csv, write_graph

def _json(value: object) -> None: print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="transformation-graph", description="Validate and query Git-native enterprise transformation graphs."); sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate"); validate.add_argument("file")
    stats = sub.add_parser("stats"); stats.add_argument("file")
    path = sub.add_parser("path"); path.add_argument("file"); path.add_argument("source"); path.add_argument("target"); path.add_argument("--undirected", action="store_true")
    context = sub.add_parser("context"); context.add_argument("file"); context.add_argument("node"); context.add_argument("--depth", type=int, default=1)
    impact = sub.add_parser("impact"); impact.add_argument("file"); impact.add_argument("node"); impact.add_argument("--depth", type=int, default=2); impact.add_argument("--direction", choices=["in","out","both"], default="both"); impact.add_argument("--relation", action="append", dest="relations")
    quality = sub.add_parser("quality"); quality.add_argument("file"); quality.add_argument("--strict", action="store_true")
    mermaid = sub.add_parser("mermaid"); mermaid.add_argument("file"); mermaid.add_argument("--focus"); mermaid.add_argument("--depth", type=int, default=1)
    import_csv = sub.add_parser("import-csv"); import_csv.add_argument("--nodes", required=True); import_csv.add_argument("--edges", required=True); import_csv.add_argument("--project-id", required=True); import_csv.add_argument("--project-name", required=True); import_csv.add_argument("--description"); import_csv.add_argument("--output", required=True)
    compose = sub.add_parser("compose"); compose.add_argument("files", nargs="+"); compose.add_argument("--project-id", required=True); compose.add_argument("--project-name", required=True); compose.add_argument("--description"); compose.add_argument("--output", required=True)
    return parser

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "import-csv":
            graph = graph_from_csv(args.nodes, args.edges, args.project_id, args.project_name, args.description); write_graph(graph, args.output); _json({"written": args.output, **graph.stats()}); return 0
        if args.command == "compose":
            graphs = [Graph.from_file(path) for path in args.files]; graph = Graph.compose(graphs, args.project_id, args.project_name, args.description); write_graph(graph, args.output); _json({"written": args.output, "sources": len(graphs), **graph.stats()}); return 0
        graph = Graph.from_file(args.file)
        if args.command == "validate": _json({"valid": True, **graph.stats()}); return 0
        if args.command == "stats": _json(graph.stats()); return 0
        if args.command == "path":
            result = graph.path(args.source, args.target, undirected=args.undirected)
            if result is None: _json({"found":False,"source":args.source,"target":args.target,"path":[]}); return 2
            _json({"found":True,"source":args.source,"target":args.target,"path":result}); return 0
        if args.command == "context": _json(graph.context(args.node, args.depth)); return 0
        if args.command == "impact": _json(graph.impact(args.node, args.depth, args.direction, set(args.relations) if args.relations else None)); return 0
        if args.command == "quality":
            report = graph.quality(); _json(report); return 3 if args.strict and not report["passed"] else 0
        if args.command == "mermaid": print(graph.mermaid(args.focus, args.depth), end=""); return 0
    except (OSError, GraphValidationError, ValueError, TypeError) as exc: print(f"ERROR: {exc}", file=sys.stderr); return 1
    return 1

if __name__ == "__main__": raise SystemExit(main())
