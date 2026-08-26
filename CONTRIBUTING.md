# Contributing

Transformation Graph is intentionally small and deterministic-first.

## Local development

```bash
python -m pip install -e ".[dev]"
pytest -q
transformation-graph validate examples/sap-s4-customer-migration.yaml
```

## Model changes

A change to the canonical model should update, in the same pull request: the JSON Schema, model docs, at least one executable example, validation logic when semantic invariants change, and tests.

Prefer additive evolution over special cases. Vendor-specific concepts should first be represented through attributes or an `x-` extension type unless they have broad enterprise value.

## Example quality

Examples should answer a real transformation question. Avoid placeholder graphs made only to demonstrate syntax. A useful example connects at least three concerns such as process + system + interface, mapping + field + rule, requirement + test + evidence, or change + decision + owner.

## Relation vocabulary

v0.1 keeps edge types open. Reuse existing relation names where they fit before inventing a synonym. If a new relation is likely to recur across projects, document it in `docs/model.md`.
