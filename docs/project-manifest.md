# Project manifest

A project manifest turns Transformation Graph from a collection of commands into one reproducible build contract.

```yaml
version: "0.1"
project:
  id: customer-domain
  name: Customer Domain
sources:
  adapters:
    - {kind: mapping, path: ../mapping.yaml}
    - {kind: interface, path: ../interface.yaml}
    - {kind: process, path: ../process.yaml}
  graphs: []
governance:
  conformance_fail_on: error
  policies: [../../policies/enterprise-baseline.yaml]
  policy_fail_on: error
  score_fail_below: 70
publish:
  site: true
```

All source and policy paths are resolved relative to the manifest file.

Run the complete pipeline with:

```bash
transformation-graph build-project transformation-project.yaml --output-dir build
```

The build performs, in order:

1. normalize every as-code source;
2. run adapter semantic conformance;
3. reconcile compatible source graphs and fail on conflicting metadata;
4. write the canonical `graph.yaml`;
5. evaluate configured policy packs;
6. calculate the governance scorecard;
7. generate the static site when enabled;
8. write `build-report.json` with source provenance, governance results, outputs, and pass/fail state.

Outputs also include `conformance.json`, `policy.json`, and `scorecard.json`. A policy threshold or score threshold can fail the command with a non-zero exit code while leaving the generated reports available for diagnosis.

`--site` / `--no-site` can override the manifest publishing flag. `--base-url` can override the site base URL, which is useful in a deployment workflow.
