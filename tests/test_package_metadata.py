from importlib.metadata import version

import transformation_graph


def test_distribution_version_matches_public_api_version():
    assert version("transformation-graph") == transformation_graph.__version__
