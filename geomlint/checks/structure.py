"""File-structure checks that operate across a file's features rather than
on a single geometry — currently just duplicate feature ids.
"""

from __future__ import annotations

from collections import Counter

from ..io import LoadedFile
from ..report import Issue, Severity


def check_duplicate_feature_ids(loaded: LoadedFile) -> list[Issue]:
    """Flag ids explicitly assigned by a user/pipeline (GeoJSON `id` member)
    that repeat within a file — a common cause of broken joins and lookups.

    Not run against Shapefile/GPKG: those ids are driver-assigned FIDs,
    guaranteed unique by the format, not user data.
    """
    issues: list[Issue] = []
    counts = Counter(f.id for f in loaded.features if f.has_explicit_id)
    for fid, count in sorted(counts.items()):
        if count > 1:
            issues.append(
                Issue(loaded.path, fid, Severity.ERROR, "duplicate-feature-id",
                      f"id '{fid}' is used by {count} features in this file — "
                      f"joins/lookups keyed on this id will silently pick the wrong one")
            )
    return issues
