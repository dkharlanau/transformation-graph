# Policy packs and PR review

Built-in quality checks cover structural invariants that make sense for almost every transformation graph. Policy packs cover expectations that vary by team, program, or lifecycle stage.

## Policy pack format

```yaml
version: "0.1"
policy:
  id: change-readiness
  name: Change readiness
  rules:
    - id: change-test-required
      kind: require_relation
      node_type: change
      direction: out
      relations: [covered_by, validated_by]
      target_type: test
      severity: error
```

v0.9 supports three deterministic rule primitives.

### `forbid_orphan`

Flags selected nodes that have no graph relationships.

### `require_attribute`

Requires an attribute on selected nodes. Dot-separated attribute paths are supported for nested objects.

```yaml
- id: interface-criticality
  kind: require_attribute
  node_type: interface
  attribute: criticality
  severity: warning
```

### `require_relation`

Requires one or more relationships matching direction, relation type, optional counterpart node type, and minimum count.

```yaml
- id: decision-owner
  kind: require_relation
  node_type: decision
  direction: out
  relations: [owned_by]
  target_type: owner
  min_count: 1
  severity: warning
```

`node_type` and `target_type` may be one type or a list. `node_type: "*"` targets every node.

## CI thresholds

```bash
transformation-graph policy graph.yaml \
  --pack policies/enterprise-baseline.yaml \
  --pack policies/change-readiness.yaml \
  --fail-on error
```

`--fail-on` accepts `error`, `warning`, or `never`. This separates report severity from CI enforcement: a policy can surface warnings without blocking delivery.

## Change review

```bash
transformation-graph review before.yaml after.yaml \
  --impact-depth 2 \
  --policy policies/change-readiness.yaml \
  --output review.md
```

The report contains:

- semantic node/edge diff
- changed roots
- deterministic attention level for changed enterprise entities
- neighboring impact at the configured depth
- built-in quality before/after and newly introduced findings
- optional policy before/after and newly introduced findings

The attention label is a triage mechanism based on node type; it is deliberately not presented as a business-risk score.

Use `--format json` for automation.

## GitHub Actions

A pull-request job can append the generated Markdown directly to `GITHUB_STEP_SUMMARY`:

```bash
git show "$BASE_SHA:path/to/graph.yaml" > /tmp/before.yaml
transformation-graph review /tmp/before.yaml path/to/graph.yaml \
  --impact-depth 2 \
  --policy policies/enterprise-baseline.yaml \
  --output /tmp/review.md
cat /tmp/review.md >> "$GITHUB_STEP_SUMMARY"
```

`.github/workflows/pr-graph-review.yml` applies this pattern to the canonical repository example so the project continuously dogfoods its own review mechanism.
