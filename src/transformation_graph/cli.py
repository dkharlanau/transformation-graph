from __future__ import annotations

import argparse
import json
import sys

from .adapters import graph_from_as_code
from .agent_context import build_context_pack, write_context_pack
from .diffing import diff_with_impact, graph_diff
from .html_export import write_html
from .importers import graph_from_csv, graph_from_excel, write_graph
from .model import Graph, GraphValidationError
from .policy import evaluate_policy_files, should_fail
from .review import build_review_report, write_review_report
from .traceability import (
    ROLE_PRESETS,
    list_role_presets,
    render_traceability_report,
    role_traceability,
    traceability_matrix,
    write_traceability_report,
)


def _json(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transformation-graph",
        description="Validate, compose, compare, govern, visualize, import, and query Git-native enterprise transformation graphs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="Validate a YAML or JSON graph."); validate.add_argument("file")
    stats = sub.add_parser("stats", help="Show graph statistics."); stats.add_argument("file")
    path = sub.add_parser("path", help="Find the shortest dependency path."); path.add_argument("file"); path.add_argument("source"); path.add_argument("target"); path.add_argument("--undirected", action="store_true")
    context = sub.add_parser("context", help="Emit bounded context around a node."); context.add_argument("file"); context.add_argument("node"); context.add_argument("--depth", type=int, default=1)
    context_pack = sub.add_parser("context-pack", help="Emit a stable agent-ready bounded context packet."); context_pack.add_argument("file"); context_pack.add_argument("node"); context_pack.add_argument("--depth", type=int, default=1); context_pack.add_argument("--output")
    impact = sub.add_parser("impact", help="Traverse impacted nodes around a root."); impact.add_argument("file"); impact.add_argument("node"); impact.add_argument("--depth", type=int, default=2); impact.add_argument("--direction", choices=["in", "out", "both"], default="both"); impact.add_argument("--relation", action="append", dest="relations")
    quality = sub.add_parser("quality", help="Run built-in graph quality checks."); quality.add_argument("file"); quality.add_argument("--strict", action="store_true")
    policy = sub.add_parser("policy", help="Evaluate configurable governance policy packs."); policy.add_argument("file"); policy.add_argument("--pack", action="append", required=True, dest="packs"); policy.add_argument("--fail-on", choices=["error", "warning", "never"], default="error")
    mermaid = sub.add_parser("mermaid", help="Export graph or focused subgraph as Mermaid."); mermaid.add_argument("file"); mermaid.add_argument("--focus"); mermaid.add_argument("--depth", type=int, default=1)
    html = sub.add_parser("html", help="Generate a dependency-free single-file HTML/SVG explorer."); html.add_argument("file"); html.add_argument("--output", required=True); html.add_argument("--title")
    trace = sub.add_parser("trace", help="Build shortest-path traceability between node types."); trace.add_argument("file"); trace.add_argument("--from-type", action="append", required=True, dest="source_types"); trace.add_argument("--to-type", action="append", required=True, dest="target_types"); trace.add_argument("--max-depth", type=int, default=4); trace.add_argument("--directed", action="store_true"); trace.add_argument("--format", choices=["json", "markdown", "csv"], default="json"); trace.add_argument("--output")
    role_view = sub.add_parser("role-view", help="Generate a role-oriented traceability view."); role_view.add_argument("file"); role_view.add_argument("role", choices=sorted(ROLE_PRESETS)); role_view.add_argument("--max-depth", type=int, default=4); role_view.add_argument("--format", choices=["json", "markdown", "csv"], default="json"); role_view.add_argument("--output")
    sub.add_parser("roles", help="List built-in role-oriented traceability presets.")
    import_csv = sub.add_parser("import-csv", help="Build a graph from node and edge CSV files."); import_csv.add_argument("--nodes", required=True); import_csv.add_argument("--edges", required=True); import_csv.add_argument("--project-id", required=True); import_csv.add_argument("--project-name", required=True); import_csv.add_argument("--description"); import_csv.add_argument("--output", required=True)
    import_excel = sub.add_parser("import-excel", help="Build a graph from an Excel workbook with Nodes and Edges sheets."); import_excel.add_argument("workbook"); import_excel.add_argument("--nodes-sheet", default="Nodes"); import_excel.add_argument("--edges-sheet", default="Edges"); import_excel.add_argument("--project-id", required=True); import_excel.add_argument("--project-name", required=True); import_excel.add_argument("--description"); import_excel.add_argument("--output", required=True)
    import_adapter = sub.add_parser("import-adapter", help="Normalize a Mapping/Interface/Process-as-Code document into the canonical graph."); import_adapter.add_argument("kind", choices=["mapping", "interface", "process"]); import_adapter.add_argument("input"); import_adapter.add_argument("--project-id"); import_adapter.add_argument("--project-name"); import_adapter.add_argument("--output", required=True)
    compose = sub.add_parser("compose", help="Compose multiple graph slices deterministically."); compose.add_argument("files", nargs="+"); compose.add_argument("--project-id", required=True); compose.add_argument("--project-name", required=True); compose.add_argument("--description"); compose.add_argument("--output", required=True)
    diff = sub.add_parser("diff", help="Compare two graph snapshots and optionally calculate neighboring impact."); diff.add_argument("before"); diff.add_argument("after"); diff.add_argument("--impact-depth", type=int, default=0)
    review = sub.add_parser("review", help="Generate a Markdown or JSON change-review report for CI/PR use."); review.add_argument("before"); review.add_argument("after"); review.add_argument("--impact-depth", type=int, default=1); review.add_argument("--policy", action="append", dest="policies"); review.add_argument("--format", choices=["markdown", "json"], default="markdown"); review.add_argument("--output", required=True)
    mcp = sub.add_parser("mcp", help="Run an MCP v2 server backed by a graph file."); mcp.add_argument("file"); mcp.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio"); mcp.add_argument("--host", default="127.0.0.1"); mcp.add_argument("--port", type=int, default=8000)
    return parser


def _emit_trace_report(report: dict, format: str, output: str | None) -> None:
    if output:
        write_traceability_report(report, output, format)  # type: ignore[arg-type]
        _json({"written": output, "format": format, "paths": report["summary"]["paths"]})
    else:
        print(render_traceability_report(report, format), end="")  # type: ignore[arg-type]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "roles":
            _json(list_role_presets()); return 0
        if args.command == "import-csv":
            graph = graph_from_csv(args.nodes, args.edges, args.project_id, args.project_name, args.description); write_graph(graph, args.output); _json({"written": args.output, **graph.stats()}); return 0
        if args.command == "import-excel":
            graph = graph_from_excel(args.workbook, args.project_id, args.project_name, args.description, nodes_sheet=args.nodes_sheet, edges_sheet=args.edges_sheet); write_graph(graph, args.output); _json({"written": args.output, **graph.stats()}); return 0
        if args.command == "import-adapter":
            graph = graph_from_as_code(args.input, args.kind, args.project_id, args.project_name); write_graph(graph, args.output); _json({"written": args.output, "adapter": args.kind, **graph.stats()}); return 0
        if args.command == "compose":
            graphs = [Graph.from_file(path) for path in args.files]; graph = Graph.compose(graphs, args.project_id, args.project_name, args.description); write_graph(graph, args.output); _json({"written": args.output, "sources": len(graphs), **graph.stats()}); return 0
        if args.command == "diff":
            before = Graph.from_file(args.before); after = Graph.from_file(args.after); report = diff_with_impact(before, after, args.impact_depth) if args.impact_depth > 0 else graph_diff(before, after); _json(report); return 0
        if args.command == "review":
            before = Graph.from_file(args.before); after = Graph.from_file(args.after); report = build_review_report(before, after, args.impact_depth, args.policies or []); write_review_report(report, args.output, args.format); _json({"written": args.output, "format": args.format, "changed_roots": len(report["changed_roots"]), "impacted_nodes": len(report["impact"]["nodes"]), "attention": report["attention_summary"]}); return 0
        if args.command == "mcp":
            try:
                from .mcp_server import run_mcp_server
            except ModuleNotFoundError as exc:
                if exc.name == "mcp": print('ERROR: MCP support is optional. Install with: pip install -e ".[mcp]"', file=sys.stderr); return 1
                raise
            run_mcp_server(args.file, transport=args.transport, host=args.host, port=args.port); return 0

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
        if args.command == "quality": report = graph.quality(); _json(report); return 3 if args.strict and not report["passed"] else 0
        if args.command == "policy": report = evaluate_policy_files(graph, args.packs); _json(report); return 4 if should_fail(report, args.fail_on) else 0
        if args.command == "mermaid": print(graph.mermaid(args.focus, args.depth), end=""); return 0
        if args.command == "html": write_html(graph, args.output, args.title); _json({"written": args.output, **graph.stats()}); return 0
        if args.command == "trace":
            report = traceability_matrix(graph, set(args.source_types), set(args.target_types), args.max_depth, undirected=not args.directed); _emit_trace_report(report, args.format, args.output); return 0
        if args.command == "role-view":
            report = role_traceability(graph, args.role, args.max_depth); _emit_trace_report(report, args.format, args.output); return 0
    except (OSError, GraphValidationError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
