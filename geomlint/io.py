"""Geo file reader — GeoJSON natively, Shapefile/GPKG via the optional `formats` extra.

GeoJSON is parsed directly with the stdlib + shapely: no GDAL, no system
dependencies. Shapefile/GPKG go through `pyogrio`, which ships GDAL inside
its own wheel — `pip install geomlint[formats]` still needs nothing on the
system beyond that.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shapely.geometry import shape
from shapely.errors import GEOSException

GEOJSON_EXTENSIONS = (".geojson", ".json")
OGR_EXTENSIONS = (".shp", ".gpkg")
ALL_EXTENSIONS = GEOJSON_EXTENSIONS + OGR_EXTENSIONS

_FORMAT_BY_EXTENSION = {
    ".geojson": "geojson",
    ".json": "geojson",
    ".shp": "shapefile",
    ".gpkg": "gpkg",
}


@dataclass
class Feature:
    id: str
    geometry: Any  # shapely geometry, or None if unparseable
    raw_geometry: dict | None
    properties: dict
    file: str
    has_explicit_id: bool = False  # True only for a user/pipeline-assigned id, not a synthesized index or driver FID


@dataclass
class LoadedFile:
    path: str
    declared_crs: str | None  # e.g. "EPSG:4326", or None if absent
    features: list[Feature]
    parse_errors: list[str]
    format: str = "geojson"  # "geojson" | "shapefile" | "gpkg"


def find_geo_files(root: str) -> list[Path]:
    p = Path(root)
    if p.is_file():
        return [p]
    found: list[Path] = []
    for ext in ALL_EXTENSIONS:
        found.extend(p.rglob(f"*{ext}"))
    return sorted(found)


def _extract_declared_crs(doc: dict) -> str | None:
    # Legacy GeoJSON CRS member (removed in RFC 7946 but still common in the wild).
    crs = doc.get("crs")
    if not crs:
        return None
    try:
        name = crs.get("properties", {}).get("name", "")
        return name or None
    except AttributeError:
        return None


def load_file(path: Path) -> LoadedFile:
    fmt = _FORMAT_BY_EXTENSION.get(path.suffix.lower())
    if fmt in ("shapefile", "gpkg"):
        return _load_ogr(path, fmt)
    return _load_geojson(path)


def _load_geojson(path: Path) -> LoadedFile:
    parse_errors: list[str] = []
    try:
        doc = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return LoadedFile(str(path), None, [], [f"could not parse JSON: {e}"], format="geojson")

    declared_crs = _extract_declared_crs(doc)

    raw_features = doc.get("features")
    if raw_features is None:
        if doc.get("type") in ("Feature", "Point", "Polygon", "LineString",
                                "MultiPolygon", "MultiLineString", "MultiPoint",
                                "GeometryCollection"):
            raw_features = [doc if doc.get("type") == "Feature" else {"type": "Feature", "geometry": doc, "properties": {}}]
        else:
            raw_features = []

    features: list[Feature] = []
    for idx, feat in enumerate(raw_features):
        has_explicit_id = "id" in feat
        fid = str(feat.get("id", idx))
        geom_json = feat.get("geometry")
        geom = None
        if geom_json is None:
            parse_errors.append(f"feature {fid}: null geometry")
        else:
            try:
                geom = shape(geom_json)
            except (GEOSException, ValueError, TypeError) as e:
                parse_errors.append(f"feature {fid}: unparseable geometry ({e})")
        features.append(
            Feature(
                id=fid,
                geometry=geom,
                raw_geometry=geom_json,
                properties=feat.get("properties") or {},
                file=str(path),
                has_explicit_id=has_explicit_id,
            )
        )

    return LoadedFile(str(path), declared_crs, features, parse_errors, format="geojson")


def _load_ogr(path: Path, fmt: str) -> LoadedFile:
    """Shapefile/GPKG loader — requires the optional `formats` extra (pyogrio)."""
    try:
        import shapely
        from pyogrio.raw import read
    except ImportError:
        return LoadedFile(
            str(path), None, [],
            [f"reading {path.suffix} files requires the optional 'formats' extra "
             f"— install with: pip install geomlint[formats]"],
            format=fmt,
        )

    try:
        meta, fids, geometry, field_data = read(str(path), return_fids=True)
    except Exception as e:
        return LoadedFile(str(path), None, [], [f"could not read {path.name}: {e}"], format=fmt)

    declared_crs = meta.get("crs") or None
    field_names = list(meta.get("fields", []))

    features: list[Feature] = []
    parse_errors: list[str] = []
    count = len(geometry) if geometry is not None else 0
    for idx in range(count):
        fid = str(fids[idx]) if fids is not None else str(idx)
        wkb = geometry[idx] if geometry is not None else None
        geom = None
        if wkb is None:
            parse_errors.append(f"feature {fid}: null geometry")
        else:
            try:
                geom = shapely.from_wkb(wkb)
            except Exception as e:
                parse_errors.append(f"feature {fid}: unparseable geometry ({e})")
        properties = {name: field_data[col][idx] for col, name in enumerate(field_names)}
        features.append(
            Feature(
                id=fid,
                geometry=geom,
                raw_geometry=None,
                properties=properties,
                file=str(path),
                has_explicit_id=False,  # driver-assigned FID, not user/pipeline data
            )
        )

    return LoadedFile(str(path), declared_crs, features, parse_errors, format=fmt)
