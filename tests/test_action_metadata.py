from pathlib import Path

import yaml


def test_root_action_metadata_is_valid_composite_action():
    metadata = yaml.safe_load(Path("action.yml").read_text(encoding="utf-8"))
    assert metadata["name"] == "Transformation Graph Adapter Conformance"
    assert metadata["runs"]["using"] == "composite"
    assert set(metadata["inputs"]) == {"kind", "input", "fail-on", "report-path", "python-version"}
    steps = metadata["runs"]["steps"]
    assert any(step.get("uses") == "actions/setup-python@v5" for step in steps)
    assert any("transformation-graph adapter-check" in step.get("run", "") for step in steps)
