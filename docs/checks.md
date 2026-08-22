# Checks reference

Every issue geomlint reports has a stable `code`, used both in the table/JSON output and in [config](configuration.md) (`disabled_checks`, `severity_overrides`).

## Geometry validity & topology

| Code | Default severity | Applies to | What it means |
|---|---|---|---|
| `unparseable-geometry` | ERROR | all formats | The feature's geometry couldn't be parsed at all (malformed JSON geometry, or a format the reader couldn't decode). |
| `empty-geometry` | ERROR | all formats | The feature has a geometry object, but it's empty (no coordinates). |
| `invalid-geometry` | ERROR | all formats | The geometry is topologically invalid per GEOS (self-intersections, collapsed rings, etc.) — shapely's `explain_validity()` reason is included in the message. |
| `zero-area-polygon` | ERROR | Polygon/MultiPolygon | The polygon's area is at or below `zero_area_epsilon` — almost certainly a collapsed ring, not "just small." |
| `zero-length-line` | ERROR | LineString/MultiLineString | The line's start and end coincide with zero length. |
| `duplicate-vertices` | WARNING | all geometry types | Consecutive vertices repeat. Harmless on its own, but a common precursor to self-intersection after the next simplify/reproject. |
| `wrong-ring-orientation` | WARNING | Polygon/MultiPolygon, **GeoJSON only** | A ring doesn't follow the RFC 7946 right-hand rule (exterior counterclockwise, holes clockwise). Not checked for Shapefile/GPKG, which don't share that convention. |
| `antimeridian-crossing-suspected` | WARNING | all non-point geometry types | The feature's bounding box spans more than 180° of longitude — almost always a feature that crosses ±180° without being split, not a genuinely huge shape. |
| `excessive-coordinate-precision` | INFO | all geometry types | A coordinate carries more decimal places than `max_coordinate_precision` — usually fake precision from a float round-trip, not real measurement accuracy. |

## CRS sanity

| Code | Default severity | Applies to | What it means |
|---|---|---|---|
| `unrecognized-crs` | ERROR | all formats | The file declares a CRS that doesn't resolve via `pyproj` — check the authority code/name. |
| `missing-crs` | WARNING | **Shapefile/GPKG only** | No CRS was found at all. Not flagged for GeoJSON, since RFC 7946 mandates WGS84 with no CRS member required. |
| `coordinates-out-of-wgs84-range` | ERROR or WARNING | all formats | Coordinates fall outside valid lon/lat bounds — very likely projected data (UTM, state plane, etc.) mislabeled or exported without reprojecting to WGS84. Severity is ERROR when more than `out_of_range_error_pct`% of features in the file are affected, WARNING otherwise. |
| `mismatched-crs-across-files` | WARNING | batch-level, across all files in one run | Two or more files in the same run declare different CRSes — an easy way to silently corrupt a spatial join if it's not intentional. |

## Structural checks

| Code | Default severity | Applies to | What it means |
|---|---|---|---|
| `duplicate-feature-id` | ERROR | GeoJSON, features with an explicit `id` member | The same user/pipeline-assigned id is used by more than one feature in the file. Not checked for Shapefile/GPKG, where ids are driver-assigned FIDs guaranteed unique by the format. |

## Not implemented

Positional/GPS-drift detection (multipath, sensor jumps) is intentionally **not** implemented as a check — see [`geomlint/checks/drift.py`](https://github.com/DBishal13/geomlint/blob/main/geomlint/checks/drift.py) for why a naive distance threshold would just be noise, and the roadmap for doing it properly. Passing `--drift` on the CLI fails loudly with that explanation rather than silently doing nothing.
