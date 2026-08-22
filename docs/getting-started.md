# Getting started

## Install

Not on PyPI yet — install straight from GitHub:

```bash
pip install "geomlint @ git+https://github.com/DBishal13/geomlint.git"              # GeoJSON only
pip install "geomlint[formats] @ git+https://github.com/DBishal13/geomlint.git"     # + Shapefile/GPKG, via pyogrio
```

The base install has no system dependencies — `shapely` and `pyproj` ship self-contained wheels. The `formats` extra pulls in `pyogrio`, which bundles its own GDAL inside the wheel, so you still don't need anything installed at the OS level to read Shapefile/GPKG.

If you're developing geomlint itself:

```bash
git clone https://github.com/DBishal13/geomlint.git && cd geomlint
pip install -e ".[dev,formats]"
pytest tests/ -v
```

## Run your first check

```bash
geomlint check ./path/to/data
```

`path` can be a single file or a directory — directories are scanned recursively for `.geojson`, `.json`, `.shp`, and `.gpkg` files. You can pass multiple paths in one invocation:

```bash
geomlint check a.geojson b.gpkg ./more_data/
```

## Reading the output

```text
SEVERITY CODE                 FILE                         FEATURE      MESSAGE
-------------------------------------------------------------------------------
ERROR    invalid-geometry     parcels/block_14.geojson      parcel-001   topologically invalid: Self-intersection[0.5 0.5]

1 issue(s) — 1 error
```

Every row is one issue: which file and feature it came from, what kind of problem it is (the `CODE` — see the [checks reference](checks.md)), and a human-readable explanation. For piping into another tool, use `--format json` instead — same fields, one JSON object per issue.

## Gating CI on it

```bash
geomlint check ./path/to/data --fail-on error     # default: only ERROR fails the build
geomlint check ./path/to/data --fail-on warning   # stricter: WARNING or ERROR fails the build
```

The exit code is `0` when nothing at or above `--fail-on` was found, and `1` otherwise — that's the whole contract a CI step needs. See [CI integration](ci-integration.md) for a drop-in GitHub Action and pre-commit hook.
