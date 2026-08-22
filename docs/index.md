---
title: geomlint
description: Continuous validity, topology, and CRS-sanity checks for vector geospatial data.
---

<div class="geomlint-hero" markdown>

# geomlint

<p class="tagline">Monte Carlo for geometry columns. The checks every mainstream data-observability tool skips, because it treats a geometry column as an opaque blob.</p>

[Get started](getting-started.md){ .md-button .md-button--primary }
[:fontawesome-brands-github: View on GitHub](https://github.com/DBishal13/geomlint){ .md-button }

</div>

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

## What it catches

<div class="grid cards" markdown>

-   :material-vector-polygon:{ .lg .middle } **Geometry &amp; topology**

    ---

    Self-intersections, collapsed rings, zero-area shapes, duplicate vertices, RFC&nbsp;7946 ring winding, antimeridian crossings, fake coordinate precision.

    [:octicons-arrow-right-24: Checks reference](checks.md)

-   :material-earth:{ .lg .middle } **CRS sanity**

    ---

    Unrecognized or missing CRS, coordinates that fall outside WGS84 bounds, mismatched CRS declarations across a batch of files.

    [:octicons-arrow-right-24: Checks reference](checks.md#crs-sanity)

-   :material-file-multiple-outline:{ .lg .middle } **GeoJSON, Shapefile, GPKG**

    ---

    GeoJSON parsed natively, no system dependencies. Shapefile/GPKG behind an optional extra — still no GDAL to install.

    [:octicons-arrow-right-24: Getting started](getting-started.md)

-   :material-cog-outline:{ .lg .middle } **Configurable, CI-native**

    ---

    `.geomlint.toml` for thresholds and severities, a `--fail-on` gate for CI, a GitHub Action, and a pre-commit hook.

    [:octicons-arrow-right-24: CI integration](ci-integration.md)

</div>

## Why this exists

Bad geometry and CRS confusion don't throw exceptions — they produce quietly wrong maps, quietly wrong joins, and quietly wrong distance calculations that nobody notices until a downstream report is off and nobody can say why.

`ST_IsValid` and friends exist in every spatial database, but they're one-off functions you have to remember to run — not a check suite that runs in CI on every pull request or pipeline load, the way `great_expectations` or a `dbt test` does for tabular data. geomlint is that check suite for the geometry column itself.

!!! info "Not yet implemented, on purpose"
    Positional/GPS-drift detection (multipath, sensor jumps) isn't a check here — see [`geomlint/checks/drift.py`](https://github.com/DBishal13/geomlint/blob/main/geomlint/checks/drift.py) for why a naive distance threshold would just be noise, and the roadmap for doing it properly.

## Where to go next

- [**Getting started**](getting-started.md) — install and run your first check.
- [**Checks reference**](checks.md) — every check code, its severity, and what it means.
- [**Configuration**](configuration.md) — tune thresholds, disable checks, override severities.
- [**CLI reference**](cli.md) — every flag and exit code.
- [**CI integration**](ci-integration.md) — GitHub Action and pre-commit hook.
