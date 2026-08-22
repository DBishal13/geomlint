from pathlib import Path

from geomlint.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_clean_dir_exits_zero(capsys):
    code = main(["check", str(FIXTURES / "clean")])
    assert code == 0
    assert "No issues found" in capsys.readouterr().out


def test_broken_dir_exits_nonzero(capsys):
    code = main(["check", str(FIXTURES / "broken")])
    assert code == 1
    assert "issue(s)" in capsys.readouterr().out


def test_multiple_paths_are_combined(capsys):
    code = main([
        "check",
        str(FIXTURES / "broken" / "bowtie_polygon.geojson"),
        str(FIXTURES / "clean" / "valid_parcels.geojson"),
        "--format", "json",
    ])
    out = capsys.readouterr().out
    assert code == 1
    assert "bowtie_polygon.geojson" in out
    assert "valid_parcels.geojson" not in out  # clean file contributes no issues


def test_config_disables_check(tmp_path, capsys):
    (tmp_path / ".geomlint.toml").write_text('disabled_checks = ["duplicate-vertices"]\n')
    code = main([
        "check", str(FIXTURES / "broken" / "bowtie_polygon.geojson"),
        "--config", str(tmp_path / ".geomlint.toml"),
    ])
    out = capsys.readouterr().out
    assert code == 1
    assert "duplicate-vertices" not in out


def test_missing_path_exits_two(capsys):
    code = main(["check", "/no/such/path/geomlint-test"])
    assert code == 2


def test_version_flag(capsys):
    try:
        main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    assert "geomlint" in capsys.readouterr().out
