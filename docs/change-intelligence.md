# Change intelligence

Git already tells us which YAML lines changed. Transformation Graph adds semantic change information: which enterprise objects changed and what sits next to those changes in the dependency graph.

## Compare two snapshots

```bash
transformation-graph diff examples/change/before.yaml examples/change/after.yaml
```

The JSON report separates added, removed, and changed nodes and edges. Stable node IDs make title, attributes, tags, and descriptions comparable without relying on file position.

## Expand to neighboring impact

```bash
transformation-graph diff \
  examples/change/before.yaml \
  examples/change/after.yaml \
  --impact-depth 1
```

`changed_roots` contains directly changed nodes plus endpoints of changed relations. Impact expansion then traverses the graph around those roots and returns neighboring nodes that may need review.

For the example, an interface title changes and SAP S/4HANA is connected as a new target. The direct roots are the interface and S/4HANA; depth-1 impact also surfaces the source ERP and the interface smoke test.

## Pull-request pattern

A practical CI pattern is:

1. Validate both graph snapshots.
2. Generate the semantic diff.
3. Expand impact one or two hops.
4. Review changed roots and impacted tests, interfaces, mappings, owners, or evidence.
5. Fail only on deterministic policy violations; keep broader impact output as review context.

This is the basis for later GitHub PR summaries and CI annotations.
