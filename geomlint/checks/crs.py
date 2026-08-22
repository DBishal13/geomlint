"""CRS sanity checks.

GeoJSON's spec (RFC 7946) says every file is WGS84 lon/lat, full stop — no
CRS member needed or honored. Reality: pipelines routinely export projected
coordinates (state plane, UTM, whatever the source system used) into a
.geojson file with no CRS declared, or a legacy `crs` member that consuming
tools may or may not respect. Both are silent corruption waiting to happen.
"""

from __future__ import annotations

from pyproj import CRS
from pyproj.exceptions import CRSError

from ..config import Config
from ..io import LoadedFile
from ..report import Issue, Severity

# A generous lon/lat envelope — flags data that could not possibly be
# WGS84 degrees, without false-positiving on legitimate edge-of-range data.
LON_RANGE = (-180.0, 180.0)
LAT_RANGE = (-90.0, 90.0)

_FORMAT_LABELS = {"shapefile": "Shapefile", "gpkg": "GeoPackage"}


def check_crs(loaded: LoadedFile, config: Config | None = None) -> list[Issue]:
    config = config or Config()
    issues: list[Issue] = []

    if loaded.declared_crs:
        try:
            CRS.from_user_input(loaded.declared_crs)
        except CRSError:
            issues.append(
                Issue(loaded.path, "-", Severity.ERROR, "unrecognized-crs",
                      f"declared CRS '{loaded.declared_crs}' does not resolve "
                      f"via pyproj — check the authority code/name")
            )
    elif loaded.format != "geojson" and not loaded.parse_errors:
        # GeoJSON has no CRS by spec (RFC 7946 mandates WGS84), so absence is
        # normal there. Shapefile/GPKG almost always carry one — a missing
        # one here means we can't sanity-check coordinates against anything.
        # Skip this when the file failed to load at all (e.g. the optional
        # 'formats' extra isn't installed) — "no CRS found" is misleading
        # noise on top of the real problem, which is that nothing was read.
        label = _FORMAT_LABELS.get(loaded.format, loaded.format)
        issues.append(
            Issue(loaded.path, "-", Severity.WARNING, "missing-crs",
                  f"no CRS found in this {label} file — cannot verify "
                  f"coordinates are in the reference system consumers expect")
        )

    out_of_range = 0
    for feature in loaded.features:
        if feature.geometry is None or feature.geometry.is_empty:
            continue
        minx, miny, maxx, maxy = feature.geometry.bounds
        if not (_in_range(minx, LON_RANGE) and _in_range(maxx, LON_RANGE)
                and _in_range(miny, LAT_RANGE) and _in_range(maxy, LAT_RANGE)):
            out_of_range += 1

    if out_of_range:
        pct = out_of_range / max(len(loaded.features), 1) * 100
        severity = Severity.ERROR if pct > config.out_of_range_error_pct else Severity.WARNING
        issues.append(
            Issue(
                loaded.path, "-", severity, "coordinates-out-of-wgs84-range",
                f"{out_of_range}/{len(loaded.features)} feature(s) have coordinates "
                f"outside valid lon/lat bounds — this file is very likely projected "
                f"data (UTM, state plane, etc.) mislabeled or exported as GeoJSON "
                f"without reprojecting to WGS84 first"
            )
        )

    return issues


def check_crs_consistency(loaded_files: list[LoadedFile]) -> list[Issue]:
    """Cross-file check: run once per batch, not per file."""
    issues: list[Issue] = []
    declared = {lf.path: lf.declared_crs for lf in loaded_files if lf.declared_crs}
    if len(set(declared.values())) > 1:
        detail = "; ".join(f"{path} → {crs}" for path, crs in declared.items())
        issues.append(
            Issue(
                "(batch)", "-", Severity.WARNING, "mismatched-crs-across-files",
                f"multiple distinct CRS declarations found in this batch: {detail} "
                f"— confirm this is intentional before joining/comparing these layers"
            )
        )
    return issues


def _in_range(value: float, bounds: tuple[float, float]) -> bool:
    return bounds[0] <= value <= bounds[1]
