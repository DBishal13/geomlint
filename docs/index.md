# geomlint

**Monte Carlo for geometry columns.** Continuous validity, topology, and CRS-sanity checks for vector geospatial data — the checks every mainstream data-observability tool (Monte Carlo, Anomalo, Great Expectations) skips because it treats a geometry column as an opaque blob.

No GDAL, no Fiona, no system dependencies to get started — a single `pip install` and it runs anywhere `pip` does. That's deliberate: this is meant to live in CI, not require a GIS environment to even install.

```text
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

- **Topologically invalid geometry** — self-intersections, collapsed rings, zero-area/zero-length shapes, duplicate vertices, ring winding order that violates RFC 7946.
- **CRS confusion** — no CRS declared, an unrecognized CRS, or coordinates that are obviously projected data (UTM meters, state plane feet) sitting in a file that claims to be WGS84 lon/lat degrees.
- **CRS drift across a batch** — two files in the same pipeline run declaring two different CRSes, an easy way to silently corrupt a spatial join.
- **Structural footguns** — duplicate feature ids within a file, fake-precision coordinates from a float round-trip, features that cross the antimeridian without being split.

**Not yet implemented, on purpose:** positional/GPS-drift detection (multipath, sensor jumps) — see the [`drift.py` source](https://github.com/DBishal13/geomlint/blob/main/geomlint/checks/drift.py) for why this is a harder statistical problem than a distance threshold, and the roadmap for doing it properly instead of faking it.

## Where to go next

- [Getting started](getting-started.md) — install and run your first check.
- [Checks reference](checks.md) — every check code, its severity, and what it means.
- [Configuration](configuration.md) — tune thresholds, disable checks, override severities.
- [CLI reference](cli.md) — every flag.
- [CI integration](ci-integration.md) — GitHub Action and pre-commit hook.
