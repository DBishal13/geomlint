# geomlint

[![test](https://github.com/DBishal13/geomlint/actions/workflows/test.yml/badge.svg)](https://github.com/DBishal13/geomlint/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

**Monte Carlo for geometry columns.** Continuous validity, topology, and CRS-sanity checks for vector geospatial data — the checks every mainstream data-observability tool (Monte Carlo, Anomalo, Great Expectations) skips because it treats a geometry column as an opaque blob.

No GDAL, no Fiona, no system dependencies to get started — a single `pip install` and it runs anywhere `pip` does, which is the point: this is meant to live in CI, not require a GIS environment to even install.

```
$ geomlint check ./parcels/
SEVERITY CODE                 FILE                         FEATURE      MESSAGE
-------------------------------------------------------------------------------
ERROR    invalid-geometry     parcels/block_14.geojson      parcel-001   topologically invalid: Self-intersection[0.5 0.5]
ERROR    coordinates-out-of-wgs84-range parcels/poles.geojson -          12/40 feature(s) outside valid lon/lat bounds — likely UTM mislabeled as WGS84
WARNING  mismatched-crs-across-files (batch) -               -          multiple distinct CRS declarations found in this batch

2 issue(s) — 1 error, 1 warning
$ echo $?
1
```

## Why this exists

Bad geometry and CRS confusion don't throw exceptions — they produce quietly wrong maps, quietly wrong joins, and quietly wrong distance calculations that nobody notices until a downstream report is off and nobody can say why. `ST_IsValid` and friends exist in every spatial database, but they're one-off functions you have to remember to run — not a check suite that runs in CI on every pull request or every pipeline load, the way `great_expectations` or a `dbt test` does for tabular data.

geomlint is that check suite, aimed at the failure modes that show up constantly in production GIS/remote-sensing pipelines:

- **Topologically invalid geometry** — self-intersections, collapsed rings, zero-area/zero-length shapes, duplicate vertices that turn into self-intersections after the next simplify or reproject, ring winding order that violates RFC 7946.
- **CRS confusion** — no CRS declared, an unrecognized CRS, or coordinates that are obviously projected data (UTM meters, state plane feet) sitting in a file that claims to be WGS84 lon/lat degrees.
- **CRS drift across a batch** — two files in the same pipeline run declaring two different CRSes, which is a very easy way to silently corrupt a spatial join.
- **Structural footguns** — duplicate feature ids within a file (broken joins/lookups), fake-precision coordinates from a float round-trip, features that cross the antimeridian without being split.

**Not yet implemented, on purpose:** positional/GPS-drift detection (multipath, sensor jumps). See `geomlint/checks/drift.py` for why this is a harder statistical problem than a distance threshold, and the roadmap for doing it properly instead of faking it.

## Install

Not on PyPI yet — install straight from GitHub:

```bash
pip install "geomlint @ git+https://github.com/DBishal13/geomlint.git"              # GeoJSON only
pip install "geomlint[formats] @ git+https://github.com/DBishal13/geomlint.git"     # + Shapefile/GPKG, via pyogrio
```

Working on this repo instead:

```bash
git clone https://github.com/DBishal13/geomlint.git && cd geomlint
pip install -e ".[dev,formats]"
```

## Use

```bash
geomlint check ./path/to/data                    # table output, human-readable
geomlint check a.geojson b.gpkg ./more_data/      # multiple files/dirs in one run
geomlint check ./path/to/data --format json       # for piping into another tool
geomlint check ./path/to/data --fail-on warning   # stricter CI gate
geomlint check ./path/to/data --config custom.toml
```

Exit code is `0` when nothing at or above `--fail-on` was found, `1` otherwise — built to drop into a CI step or a pipeline's post-load validation, not just to be read by a human.

### Config

Drop a `.geomlint.toml` in the repo (or use `[tool.geomlint]` in `pyproject.toml`) — geomlint finds it by walking up from the path you scan:

```toml
zero_area_epsilon = 1e-9          # default 1e-12
out_of_range_error_pct = 30       # default 50 — % of features out-of-range before it's an error, not a warning
max_coordinate_precision = 6      # default 7 decimal places
disabled_checks = ["wrong-ring-orientation"]
severity_overrides = { "duplicate-feature-id" = "warning" }
exclude = ["**/scratch/**"]
```

### GitHub Actions

```yaml
- uses: DBishal13/geomlint@v0.1.0
  with:
    path: ./data
    fail-on: warning  # optional, default: error
    extras: formats   # optional, e.g. for Shapefile/GPKG
```

### Pre-commit

```yaml
- repo: https://github.com/DBishal13/geomlint
  rev: v0.1.0
  hooks:
    - id: geomlint
```

## Status

Early but usable. Geometry-validity, CRS-sanity, and structural checks work and are tested against planted fixtures across GeoJSON, Shapefile, and GPKG; drift detection is intentionally stubbed. Issues and PRs welcome.

## License

MIT
