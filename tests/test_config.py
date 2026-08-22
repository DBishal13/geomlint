from pathlib import Path

import pytest

from geomlint.config import Config, load_config
from geomlint.report import Issue, Severity, apply_config

FIXTURES = Path(__file__).parent / "fixtures"


def test_no_config_file_returns_defaults(tmp_path):
    config = load_config(None, str(tmp_path))
    assert config == Config()


def test_explicit_config_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nope.toml"), str(tmp_path))


def test_geomlint_toml_overrides_thresholds(tmp_path):
    (tmp_path / ".geomlint.toml").write_text(
        "max_coordinate_precision = 3\n"
        "disabled_checks = [\"wrong-ring-orientation\"]\n"
        "severity_overrides = { \"duplicate-vertices\" = \"error\" }\n"
    )
    config = load_config(None, str(tmp_path))
    assert config.max_coordinate_precision == 3
    assert config.disabled_checks == {"wrong-ring-orientation"}
    assert config.severity_overrides == {"duplicate-vertices": "error"}


def test_pyproject_tool_geomlint_table(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[tool.geomlint]\nzero_area_epsilon = 1e-6\n"
    )
    config = load_config(None, str(tmp_path))
    assert config.zero_area_epsilon == 1e-6


def test_unknown_key_raises(tmp_path):
    (tmp_path / ".geomlint.toml").write_text("not_a_real_key = true\n")
    with pytest.raises(ValueError, match="unknown geomlint config key"):
        load_config(None, str(tmp_path))


def test_invalid_severity_override_raises(tmp_path):
    (tmp_path / ".geomlint.toml").write_text(
        "severity_overrides = { \"invalid-geometry\" = \"critical\" }\n"
    )
    with pytest.raises(ValueError, match="invalid severity"):
        load_config(None, str(tmp_path))


def test_apply_config_filters_disabled_checks():
    issues = [Issue("f.geojson", "1", Severity.ERROR, "invalid-geometry", "msg")]
    config = Config(disabled_checks={"invalid-geometry"})
    assert apply_config(issues, config) == []


def test_apply_config_remaps_severity():
    issues = [Issue("f.geojson", "1", Severity.WARNING, "duplicate-vertices", "msg")]
    config = Config(severity_overrides={"duplicate-vertices": "error"})
    result = apply_config(issues, config)
    assert result[0].severity == Severity.ERROR
