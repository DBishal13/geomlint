"""Geometry validity and topology checks.

Every check here answers a question a mainstream data-quality tool never
asks: is this geometry actually a legal shape, not just a well-formed blob
of JSON.
"""

from __future__ import annotations

import shapely
from shapely.validation import explain_validity
from shapely.geometry.base import BaseGeometry

from ..config import Config
from ..io import Feature, LoadedFile
from ..report import Issue, Severity

# Antimeridian: a bbox this wide in longitude almost certainly means a
# feature was drawn straddling +/-180 without splitting, not a genuinely
# huge shape (nothing on Earth's surface should span more than this).
ANTIMERIDIAN_BBOX_WIDTH = 180.0

# Coordinate precision tolerance: floats round-tripped through JSON parsing
# are exact to the written literal, so this only needs to clear float noise,
# not measurement error.
_PRECISION_TOLERANCE = 1e-9


def check_geometry(loaded: LoadedFile, config: Config | None = None) -> list[Issue]:
    config = config or Config()
    issues: list[Issue] = []

    for err in loaded.parse_errors:
        issues.append(
            Issue(loaded.path, "-", Severity.ERROR, "unparseable-geometry", err)
        )

    for feature in loaded.features:
        geom = feature.geometry
        if geom is None:
            continue
        issues.extend(_check_feature(loaded.path, feature, geom, loaded.format, config))

    return issues


def _check_feature(
    path: str, feature: Feature, geom: BaseGeometry, fmt: str, config: Config
) -> list[Issue]:
    issues: list[Issue] = []

    if geom.is_empty:
        issues.append(
            Issue(path, feature.id, Severity.ERROR, "empty-geometry",
                  "geometry is present but empty")
        )
        return issues

    if not geom.is_valid:
        reason = explain_validity(geom)
        issues.append(
            Issue(path, feature.id, Severity.ERROR, "invalid-geometry",
                  f"topologically invalid: {reason}")
        )

    geom_type = geom.geom_type
    if geom_type in ("Polygon", "MultiPolygon"):
        if geom.area <= config.zero_area_epsilon:
            issues.append(
                Issue(path, feature.id, Severity.ERROR, "zero-area-polygon",
                      "polygon has effectively zero area — likely a collapsed ring")
            )

    if geom_type in ("LineString", "MultiLineString") and geom.length <= 0:
        issues.append(
            Issue(path, feature.id, Severity.ERROR, "zero-length-line",
                  "line has zero length — start and end coincide")
        )

    dup = _duplicate_consecutive_vertices(geom)
    if dup:
        issues.append(
            Issue(path, feature.id, Severity.WARNING, "duplicate-vertices",
                  f"{dup} duplicate consecutive vertex pair(s) — common cause of "
                  f"downstream self-intersection after simplification/reprojection")
        )

    if fmt == "geojson" and geom_type in ("Polygon", "MultiPolygon"):
        backwards = _rings_with_wrong_orientation(geom)
        if backwards:
            issues.append(
                Issue(path, feature.id, Severity.WARNING, "wrong-ring-orientation",
                      f"{backwards} ring(s) don't follow the RFC 7946 right-hand rule "
                      f"(exterior counterclockwise, holes clockwise) — some consumers "
                      f"render or wind these incorrectly")
            )

    minx, miny, maxx, maxy = geom.bounds
    if geom_type not in ("Point", "MultiPoint") and (maxx - minx) > ANTIMERIDIAN_BBOX_WIDTH:
        issues.append(
            Issue(path, feature.id, Severity.WARNING, "antimeridian-crossing-suspected",
                  f"bounding box spans {maxx - minx:.1f} degrees of longitude — likely "
                  f"a feature crossing +/-180 that wasn't split, producing a shape that "
                  f"wraps the wrong way around the globe")
        )

    excess = _max_excess_precision(geom, config.max_coordinate_precision)
    if excess:
        issues.append(
            Issue(path, feature.id, Severity.INFO, "excessive-coordinate-precision",
                  f"coordinates carry more than {config.max_coordinate_precision} decimal "
                  f"places (up to {excess}) — likely fake precision from a float "
                  f"round-trip rather than real measurement accuracy")
        )

    return issues


def _duplicate_consecutive_vertices(geom: BaseGeometry) -> int:
    coords_list = _all_coord_sequences(geom)
    total = 0
    for coords in coords_list:
        for a, b in zip(coords, coords[1:]):
            if a == b:
                total += 1
    return total


def _rings_with_wrong_orientation(geom: BaseGeometry) -> int:
    polygons = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    backwards = 0
    for poly in polygons:
        if not shapely.is_ccw(poly.exterior):
            backwards += 1
        for interior in poly.interiors:
            if shapely.is_ccw(interior):
                backwards += 1
    return backwards


def _max_excess_precision(geom: BaseGeometry, max_places: int) -> int:
    """Return the largest number of decimal places found beyond max_places, or 0."""
    worst = 0
    tolerance = max(_PRECISION_TOLERANCE, 10 ** -(max_places + 3))
    for coords in _all_coord_sequences(geom):
        for point in coords:
            for value in point:
                places = _decimal_places(value, max_places, tolerance)
                if places > worst:
                    worst = places
    return worst if worst > max_places else 0


def _decimal_places(value: float, max_places: int, tolerance: float) -> int:
    for places in range(max_places, max_places + 8):
        if abs(value - round(value, places)) <= tolerance:
            return places
    return max_places + 8


def _all_coord_sequences(geom: BaseGeometry) -> list[list[tuple]]:
    gt = geom.geom_type
    if gt == "Point":
        return [list(geom.coords)]
    if gt in ("LineString", "LinearRing"):
        return [list(geom.coords)]
    if gt == "Polygon":
        rings = [list(geom.exterior.coords)]
        rings += [list(r.coords) for r in geom.interiors]
        return rings
    if gt.startswith("Multi") or gt == "GeometryCollection":
        out = []
        for part in geom.geoms:
            out.extend(_all_coord_sequences(part))
        return out
    return []
