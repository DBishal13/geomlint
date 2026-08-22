"""geomlint CLI — `geomlint check <path>`."""

from __future__ import annotations

import argparse
import fnmatch
import sys

from . import __version__
from .config import load_config
from .io import find_geo_files, load_file
from .checks.geometry import check_geometry
from .checks.crs import check_crs, check_crs_consistency
from .checks.structure import check_duplicate_feature_ids
from .checks.drift import check_drift, DriftCheckNotImplemented
from .report import Issue, Severity, apply_config, filter_at_or_above, render_table, render_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geomlint",
        description="Continuous validity, topology, and CRS-sanity checks for vector geospatial data.",
    )
    parser.add_argument("--version", action="version", version=f"geomlint {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Run checks against files or directories of geo data.")
    check.add_argument(
        "paths", nargs="+",
        help="Files or directories to scan (recurses for .geojson/.json, "
             ".shp/.gpkg with the 'formats' extra installed)."
    )
    check.add_argument("--format", choices=["table", "json"], default="table")
    check.add_argument(
        "--fail-on", choices=["error", "warning", "info"], default="error",
        help="Exit non-zero if any issue at or above this severity is found. "
             "Set to a level CI can gate on.",
    )
    check.add_argument(
        "--config", metavar="PATH",
        help="Path to a .geomlint.toml (or pyproject.toml [tool.geomlint]) config file. "
             "If omitted, geomlint searches upward from the scan path for one.",
    )
    check.add_argument(
        "--drift", action="store_true",
        help="Attempt positional drift detection (not yet implemented — will error clearly).",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        return _run_check(args)

    parser.print_help()
    return 1


def _run_check(args) -> int:
    try:
        config = load_config(args.config, args.paths[0])
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    files = []
    seen = set()
    for path in args.paths:
        for f in find_geo_files(path):
            if f not in seen:
                seen.add(f)
                files.append(f)
    if config.exclude:
        files = [f for f in files if not _is_excluded(f, config.exclude)]
    if not files:
        print(f"No .geojson/.json/.shp/.gpkg files found under: {', '.join(args.paths)}", file=sys.stderr)
        return 2

    loaded_files = [load_file(f) for f in files]

    issues: list[Issue] = []
    for lf in loaded_files:
        issues.extend(check_geometry(lf, config))
        issues.extend(check_crs(lf, config))
        issues.extend(check_duplicate_feature_ids(lf))
    issues.extend(check_crs_consistency(loaded_files))

    issues = apply_config(issues, config)

    if args.drift:
        try:
            check_drift()
        except DriftCheckNotImplemented as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

    output = render_json(issues) if args.format == "json" else render_table(issues)
    print(output)

    floor = Severity(args.fail_on)
    blocking = filter_at_or_above(issues, floor)
    return 1 if blocking else 0


def _is_excluded(path, patterns: list[str]) -> bool:
    posix = path.as_posix()
    return any(fnmatch.fnmatch(posix, pat) for pat in patterns)


if __name__ == "__main__":
    sys.exit(main())
