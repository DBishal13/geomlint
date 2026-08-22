# Configuration

geomlint runs with sane defaults out of the box — config is only needed to change behavior, never to make the tool work.

## Where config lives

Drop a `.geomlint.toml` file anywhere at or above the path you scan, or add a `[tool.geomlint]` table to a `pyproject.toml`. geomlint auto-discovers it by walking upward from the scan path to the filesystem root — the first match wins, `.geomlint.toml` taking priority over `pyproject.toml` in the same directory. You can also point at a specific file explicitly:

```bash
geomlint check ./data --config custom.toml
```

An explicit `--config` path must exist, or geomlint exits with an error rather than silently falling back to defaults.

## Keys

```toml
zero_area_epsilon = 1e-9
out_of_range_error_pct = 30
max_coordinate_precision = 6
disabled_checks = ["wrong-ring-orientation"]
severity_overrides = { "duplicate-feature-id" = "warning" }
exclude = ["**/scratch/**"]
```

| Key | Type | Default | Meaning |
|---|---|---|---|
| `zero_area_epsilon` | float | `1e-12` | A polygon at or below this area (in the geometry's own units — decimal degrees for lon/lat data) is flagged `zero-area-polygon`. |
| `out_of_range_error_pct` | float | `50.0` | Percentage of a file's features that must be outside WGS84 bounds before `coordinates-out-of-wgs84-range` is ERROR instead of WARNING. |
| `max_coordinate_precision` | int | `7` | Decimal places beyond which a coordinate is flagged `excessive-coordinate-precision` (7 places ≈ 1cm at the equator). |
| `disabled_checks` | list of strings | `[]` | Check codes to drop from output entirely. See the [checks reference](checks.md) for valid codes. |
| `severity_overrides` | table of string → string | `{}` | Remap a check code's severity to `"error"`, `"warning"`, or `"info"`. |
| `exclude` | list of glob strings | `[]` | Files matching any pattern (matched against the scanned path, e.g. `tests/fixtures/broken/legacy_crs_a.geojson`) are skipped entirely — no issues, and excluded from cross-file checks like `mismatched-crs-across-files`. |

An unknown key, or an invalid severity value in `severity_overrides`, is a hard error at startup — geomlint won't silently ignore a typo in your config.

## Precedence

1. `--config <path>` — used as-is, must exist.
2. `.geomlint.toml`, found by walking up from the scan path.
3. `[tool.geomlint]` in a `pyproject.toml`, found the same way.
4. If nothing is found: the compiled-in defaults above.
