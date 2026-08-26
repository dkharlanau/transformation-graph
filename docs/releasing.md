# Releasing Transformation Graph

The repository is release-ready but does not publish automatically from ordinary pushes.

## Build locally

```bash
python -m pip install -e ".[dev]"
python -m build
```

A successful build produces one wheel and one source distribution in `dist/`.

## Release contract

1. Update the version in `pyproject.toml` and `src/transformation_graph/__init__.py`.
2. Update `CHANGELOG.md`.
3. Merge with CI green, including package build verification.
4. Create and push an exact matching tag, for example `v0.13.0` for package version `0.13.0`.
5. `.github/workflows/release.yml` verifies that the tag matches the package version, builds wheel + sdist, generates `SHA256SUMS`, and creates the GitHub Release with generated release notes.

The workflow uses `gh release create --verify-tag`, so it refuses to create a release from a mismatched or absent tag.

## PyPI

PyPI publishing is deliberately not enabled yet. Add trusted publishing only after the package name, public API, and release cadence are intentionally accepted. GitHub Releases can therefore mature independently without requiring registry credentials.
