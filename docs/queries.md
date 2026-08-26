# Query recipes

Use the bundled example:

```bash
pip install -e ".[dev]"
transformation-graph validate examples/sap-s4-customer-migration.yaml
```

## Inventory

```bash
transformation-graph stats examples/sap-s4-customer-migration.yaml
```

The output is JSON so it can be consumed by shell scripts, CI, agents, or documentation generators.

## Dependency path

```bash
transformation-graph path examples/sap-s4-customer-migration.yaml change.bp-model rule.id-conversion
```

For impact analysis, relationships are often traversed in either direction:

```bash
transformation-graph path examples/sap-s4-customer-migration.yaml evidence.mapping-workbook system.s4 --undirected
```

## Agent context

```bash
transformation-graph context examples/sap-s4-customer-migration.yaml mapping.customer-to-bp --depth 1
```

This gives an AI agent a bounded, deterministic context packet instead of a large unstructured project dump.

## CI gate

```bash
transformation-graph validate path/to/project.yaml
pytest
```

The repository CI runs both against the canonical example.
