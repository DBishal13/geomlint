"""Shapefile/GPKG support — skipped entirely if the optional `formats` extra
(pyogrio) isn't installed, matching how the CLI degrades in that case.
"""

from pathlib import Path

import pytest

pytest.importorskip("pyogrio")

from geomlint.io import load_file
from geomlint.checks.geometry import check_geometry
from geomlint.checks.crs import check_crs

FIXTURES = Path(__file__).parent / "fixtures" / "formats"


def test_gpkg_loads_and_flags_invalid_geometry():
    lf = load_file(FIXTURES / "parcels.gpkg")
    assert lf.format == "gpkg"
    assert lf.declared_crs == "EPSG:4326"
    assert len(lf.features) == 2

    issues = check_geometry(lf)
    codes = {i.code for i in issues}
    assert "invalid-geometry" in codes


def test_shapefile_with_no_crs_flags_missing_crs_and_projected_coords():
    lf = load_file(FIXTURES / "utm_no_crs.shp")
    assert lf.format == "shapefile"
    assert lf.declared_crs is None

    issues = check_crs(lf)
    codes = {i.code for i in issues}
    assert "missing-crs" in codes
    assert "coordinates-out-of-wgs84-range" in codes
