# Quality and impact analysis

A transformation graph becomes useful when it can detect missing project relationships, not only store them.

## Quality checks

```bash
transformation-graph quality examples/sap-s4-customer-migration.yaml
```

v0.2 starts with a deliberately small quality vocabulary:

| Finding | Meaning |
| --- | --- |
| `ORPHAN_NODE` | Node has no incoming or outgoing relationships |
| `MAPPING_WITHOUT_EVIDENCE` | Mapping has no `evidenced_by` relation |
| `DECISION_WITHOUT_OWNER` | Decision has no `owned_by` relation to an owner |
| `CHANGE_WITHOUT_TEST` | Change has no direct `covered_by` or `validated_by` relation to a test |
| `TEST_WITHOUT_TARGET` | Test does not `validate` or `cover` another node |

These checks are opinionated project hygiene, not universal enterprise truth. They are separate from structural validation for that reason.

Use strict mode in a project that wants to gate on them:

```bash
transformation-graph quality project.yaml --strict
```

Strict mode exits with code `3` when any quality finding exists.

## Impact traversal

```bash
transformation-graph impact examples/sap-s4-customer-migration.yaml change.bp-model --depth 2
```

Control direction with `--direction in|out|both`. Restrict traversal with repeated `--relation` arguments.

## Mermaid export

```bash
transformation-graph mermaid examples/sap-s4-customer-migration.yaml
transformation-graph mermaid examples/sap-s4-customer-migration.yaml --focus mapping.customer-to-bp --depth 1
```

The output can be pasted into GitHub Markdown Mermaid blocks or redirected to a `.mmd` file.
