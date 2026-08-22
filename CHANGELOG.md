# Changelog

## 0.1.0

Initial release.

- **Geometry validity & topology**: self-intersections, collapsed rings, zero-area/zero-length shapes, duplicate consecutive vertices, ring winding order (RFC 7946), antimeridian crossings that weren't split, excessive/fake coordinate precision.
- **CRS sanity**: unrecognized CRS, missing CRS (Shapefile/GPKG), coordinates out of WGS84 lon/lat range (e.g. UTM mislabeled as WGS84), mismatched CRS declarations across a batch of files.
- **Structural checks**: duplicate feature ids within a file.
- **Input formats**: GeoJSON natively (no GDAL, no system dependencies); Shapefile/GPKG behind the optional `formats` extra, via `pyogrio` (still no system GDAL).
- **Config**: `.geomlint.toml`, or `[tool.geomlint]` in `pyproject.toml`, auto-discovered upward from the scan path (or `--config`). Tunes thresholds, disables specific checks, overrides severities, excludes path globs.
- **CLI**: `geomlint check <path...>` — multiple files/directories in one run, table/JSON output, `--fail-on` severity gate for CI, `--version`.
- **Ecosystem**: a composite GitHub Action (`uses: DBishal13/geomlint@v0.1.0`) and a pre-commit hook, both installing straight from this repo.
- **Not yet implemented, on purpose**: positional/GPS-drift detection (multipath, sensor jumps) — see `geomlint/checks/drift.py` for the roadmap and why it's a harder statistical problem than a distance threshold.
