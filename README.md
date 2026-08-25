# Transformation Graph

Build project-scoped enterprise transformation graphs across processes, systems, data, interfaces, mappings, tests, and changes.

## Problem

Transformation knowledge is fragmented across PowerPoint, Excel, architecture diagrams, process documentation, mappings, Jira, and people's heads.

## Core idea

Model processes, process steps, systems, business objects, data objects, mappings, interfaces, business rules, requirements, tests, owners, decisions, and changes as one project-scoped graph stored in Git.

## Example

```text
Process
  -> uses Data Object
  -> runs in System
  -> sends through Interface
  -> uses Mapping
  -> covered by Test
  -> affected by Change
```

## Initial scope

- ingest YAML/JSON/CSV/Excel
- build graph
- interactive visual traversal
- filtering
- dependency paths
- impact views
- orphan detection
- export graph data
- Markdown/JSON context output

## Long-term direction

A lightweight, project-scoped enterprise transformation model stored in Git.

## Design principles

- versionable
- portable
- machine-readable
- deterministic-first
- visual where useful
- Git-friendly
- vendor-neutral where practical
- interoperable with enterprise tools

## Status

Planning.
