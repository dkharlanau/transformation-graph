# Adapter contract v0.1

`transformation-graph-adapter/v0.1` is the semantic compatibility contract between Transformation Graph and Mapping/Interface/Process-as-Code sources.

The authoritative packaged contract is available with:

```bash
transformation-graph adapter-contract --format yaml
```

The immutable cross-repository fixtures live under `conformance/adapter-v0.1/`, and `schema/adapter-conformance-report.schema.json` defines the machine-readable report shape.

## Reusable GitHub Action

Sibling repositories can run the same checker without copying its implementation:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: dkharlanau/transformation-graph@<release-tag-or-commit-sha>
    with:
      kind: mapping
      input: examples/mapping.yaml
      fail-on: error
      report-path: conformance-report.json
```

Use `kind: interface` or `kind: process` for the other adapters.

Until a public release tag is intentionally created, pin the Action to an exact commit SHA. After releases begin, pin to an explicit release tag rather than `main` for reproducible contract behavior.

## Compatibility semantics

Mapping normalization requires a mapping root, source/target data objects, and field rules whose `reads` / `writes` relationships connect source and target fields.

Interface normalization requires an interface root and source/target system relationships. Ownership and validating tests are recommended and produce warnings when absent.

Process normalization requires a process with contained steps. A declared start must resolve, and contained steps should be reachable from it. User tasks should identify an actor; service tasks should identify a system and/or interface.

Conformance errors represent contract-required semantics. Warnings represent recommended governance/execution semantics. Reconciled composition still fails loudly on incompatible same-ID metadata even when the individual adapters pass conformance.
