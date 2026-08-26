# Mapping as Code integration

Transformation Graph can consume a deterministic graph projection produced by [Mapping as Code](https://github.com/dkharlanau/mapping-as-code).

```bash
map-code project mapping.yaml \
  --target transformation-graph \
  --output mapping.transformation-graph.json
```

The projection follows this repository's `schema/transformation-graph.schema.json` shape:

- source and target applications become `system` nodes;
- mapped business objects become `business_object` nodes;
- source/target fields become `field` nodes;
- the mapping set and stable field mapping rules become `mapping` nodes;
- `input_to` and `maps_to` edges retain field-level lineage;
- transform, rule, and business metadata remain on mapping nodes.

Mapping as Code remains the source of truth for mapping intent. Transformation Graph owns project-wide composition, traceability, governance, and graph analysis.

This boundary avoids maintaining the same field mapping independently in two repositories while still allowing it to participate in a larger transformation graph.
