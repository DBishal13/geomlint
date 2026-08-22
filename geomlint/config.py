"""geomlint configuration — thresholds, per-check enable/disable, severity overrides.

Looked up automatically so a team's tolerance lives in the repo instead of
CLI flags: an explicit `--config <path>` wins, otherwise geomlint searches
upward from the scan path for `.geomlint.toml`, or a `[tool.geomlint]` table
in `pyproject.toml`. Absent any config file, geomlint runs with the same
defaults it always has — config only changes behavior, it isn't required
to make the tool work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.9/3.10
    import tomli as tomllib  # type: ignore[no-redef]

from .report import Severity

DEFAULT_ZERO_AREA_EPSILON = 1e-12
DEFAULT_OUT_OF_RANGE_ERROR_PCT = 50.0
DEFAULT_MAX_COORDINATE_PRECISION = 7  # ~1cm at the equator, in decimal degrees

CONFIG_FILENAME = ".geomlint.toml"

_KNOWN_KEYS = {
    "zero_area_epsilon",
    "out_of_range_error_pct",
    "max_coordinate_precision",
    "disabled_checks",
    "severity_overrides",
    "exclude",
}


@dataclass
class Config:
    zero_area_epsilon: float = DEFAULT_ZERO_AREA_EPSILON
    out_of_range_error_pct: float = DEFAULT_OUT_OF_RANGE_ERROR_PCT
    max_coordinate_precision: int = DEFAULT_MAX_COORDINATE_PRECISION
    disabled_checks: set[str] = field(default_factory=set)
    severity_overrides: dict[str, str] = field(default_factory=dict)
    exclude: list[str] = field(default_factory=list)

    def is_enabled(self, code: str) -> bool:
        return code not in self.disabled_checks


def find_config_file(scan_path: str) -> Path | None:
    start = Path(scan_path).resolve()
    current = start if start.is_dir() else start.parent
    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        pyproject = current / "pyproject.toml"
        if pyproject.is_file() and _has_geomlint_table(pyproject):
            return pyproject
        if current.parent == current:
            return None
        current = current.parent


def _has_geomlint_table(pyproject: Path) -> bool:
    try:
        data = tomllib.loads(pyproject.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return False
    return "geomlint" in data.get("tool", {})


def load_config(explicit_path: str | None, scan_path: str) -> Config:
    if explicit_path:
        path = Path(explicit_path)
        if not path.is_file():
            raise FileNotFoundError(f"config file not found: {explicit_path}")
    else:
        path = find_config_file(scan_path)
        if path is None:
            return Config()

    try:
        data = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"could not parse {path}: {e}") from e

    section = data.get("tool", {}).get("geomlint", {}) if path.name == "pyproject.toml" else data

    unknown = set(section) - _KNOWN_KEYS
    if unknown:
        raise ValueError(
            f"unknown geomlint config key(s) in {path}: {', '.join(sorted(unknown))} "
            f"— valid keys are: {', '.join(sorted(_KNOWN_KEYS))}"
        )

    valid_severities = {s.value for s in Severity}
    severity_overrides = section.get("severity_overrides", {})
    for code, sev in severity_overrides.items():
        if sev not in valid_severities:
            raise ValueError(
                f"invalid severity '{sev}' for check '{code}' in {path} "
                f"— must be one of {sorted(valid_severities)}"
            )

    return Config(
        zero_area_epsilon=section.get("zero_area_epsilon", DEFAULT_ZERO_AREA_EPSILON),
        out_of_range_error_pct=section.get("out_of_range_error_pct", DEFAULT_OUT_OF_RANGE_ERROR_PCT),
        max_coordinate_precision=section.get("max_coordinate_precision", DEFAULT_MAX_COORDINATE_PRECISION),
        disabled_checks=set(section.get("disabled_checks", [])),
        severity_overrides=dict(severity_overrides),
        exclude=list(section.get("exclude", [])),
    )
