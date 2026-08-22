"""Pytest coverage mirroring the manual fixture run — keeps the CLI honest in CI."""

from pathlib import Path

from geomlint.io import LoadedFile, load_file
from geomlint.checks.geometry import check_geometry
from geomlint.checks.crs import check_crs, check_crs_consistency
from geomlint.checks.structure import check_duplicate_feature_ids

FIXTURES = Path(__file__).parent / "fixtures"


def _codes(issues):
    return {i.code for i in issues}


def test_bowtie_polygon_flagged_invalid():
    lf = load_file(FIXTURES / "broken" / "bowtie_polygon.geojson")
    issues = check_geometry(lf)
    by_feature = {}
    for i in issues:
        by_feature.setdefault(i.feature_id, set()).add(i.code)

    assert "invalid-geometry" in by_feature["parcel-001"]
    assert "zero-area-polygon" in by_feature["parcel-002"]
    assert "duplicate-vertices" in by_feature["parcel-003"]
    assert "parcel-004" not in by_feature  # clean control feature, no issues


def test_utm_coords_flagged_out_of_range():
    lf = load_file(FIXTURES / "broken" / "utm_mislabeled_as_wgs84.geojson")
    issues = check_crs(lf)
    assert "coordinates-out-of-wgs84-range" in _codes(issues)


def test_mismatched_crs_across_batch():
    a = load_file(FIXTURES / "broken" / "legacy_crs_a.geojson")
    b = load_file(FIXTURES / "broken" / "legacy_crs_b.geojson")
    issues = check_crs_consistency([a, b])
    assert "mismatched-crs-across-files" in _codes(issues)


def test_clean_fixture_has_no_issues():
    lf = load_file(FIXTURES / "clean" / "valid_parcels.geojson")
    issues = check_geometry(lf) + check_crs(lf) + check_duplicate_feature_ids(lf)
    assert issues == []


def test_structural_defects_flagged():
    lf = load_file(FIXTURES / "broken" / "structural_defects.geojson")
    issues = check_geometry(lf) + check_duplicate_feature_ids(lf)
    by_feature = {}
    for i in issues:
        by_feature.setdefault(i.feature_id, set()).add(i.code)

    assert "duplicate-feature-id" in by_feature["dup-01"]
    assert "wrong-ring-orientation" in by_feature["backwards-ring"]
    assert "excessive-coordinate-precision" in by_feature["high-precision-point"]
    assert "antimeridian-crossing-suspected" in by_feature["antimeridian-crosser"]
    assert "structural-control" not in by_feature  # clean control feature, no issues


def test_unreadable_shapefile_does_not_also_claim_missing_crs():
    # A shapefile that failed to load at all (e.g. the optional 'formats'
    # extra isn't installed) shouldn't ALSO get a "missing-crs" warning on
    # top of the real error — that's misleading noise, not a second finding.
    lf = LoadedFile(
        "parcels.shp", None, features=[],
        parse_errors=["reading .shp files requires the optional 'formats' extra"],
        format="shapefile",
    )
    issues = check_crs(lf)
    assert "missing-crs" not in _codes(issues)
