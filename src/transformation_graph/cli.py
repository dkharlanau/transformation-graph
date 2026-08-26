from __future__ import annotations

import argparse
import json
import sys

from .model import Graph, GraphValidationError


def _json(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transformation-graph",
        description="Validate and query Git-native enterprise transformation graphs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a YAML or JSON graph.")
    validate.add_argument("file")

    stats = sub.add_parser("stats", help="Show graph statistics.")
    stats.add_argument("file")

    path = sub.add_parser("path", help="Find the shortest dependency path.")
    path.add_argument("file")
    path.add_argument("source")
    path.add_argument("target")
    path.add_argument("--undirected", action="store_true", help="Traverse relations both ways.")

    context = sub.add_parser("context", help="Emit machine-readable context around a node.")
    context.add_argument("file")
    context.add_argument("node")
    context.add_argument("--depth", type=int, default=1)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        graph = Graph.from_file(args.file)

        if args.command == "validate":
            _json({"valid": True, **graph.stats()})
            return 0

        if args.command == "stats":
            _json(graph.stats())
            return 0

        if args.command == "path":
            result = graph.path(args.source, args.target, undirected=args.undirected)
            if result is None:
                _json({"found": False, "source": args.source, "target": args.target, "path": []})
                return 2
            _json({"found": True, "source": args.source, "target": args.target, "path": result})
            return 0

        if args.command == "context":
            _json(graph.context(args.node, depth=args.depth))
            return 0

    except (OSError, GraphValidationError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
