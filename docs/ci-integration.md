# CI integration

Both integrations below install straight from this repo's git history rather than PyPI — that means you can pin to any tag, branch, or commit, not just released versions, and pick up a fix before it's cut into a release.

## GitHub Actions

```yaml
- uses: DBishal13/geomlint@v0.1.0
  with:
    path: ./data
    fail-on: warning  # optional, default: error
    extras: formats   # optional, e.g. for Shapefile/GPKG
```

### Inputs

| Input | Default | Meaning |
|---|---|---|
| `path` | `.` | File(s)/directory to scan. Space-separated for multiple. |
| `fail-on` | `error` | Passed straight through to `--fail-on`. |
| `format` | `table` | Passed straight through to `--format`. |
| `config` | *(unset)* | Path to a `.geomlint.toml`. Omit to let geomlint auto-discover one. |
| `extras` | *(unset)* | Comma-separated optional extras to install, e.g. `formats` for Shapefile/GPKG support. |
| `ref` | *(unset)* | geomlint git ref (tag/branch/commit) to install. Defaults to the latest commit on the default branch — pin this (e.g. to a tag) for a reproducible build. |

The action installs geomlint fresh on every run (`pip install "geomlint @ git+https://github.com/DBishal13/geomlint.git@<ref>"`), then runs `geomlint check` with the inputs above.

## Pre-commit

```yaml
- repo: https://github.com/DBishal13/geomlint
  rev: v0.1.0
  hooks:
    - id: geomlint
```

The hook runs `geomlint check` against whatever `.geojson`, `.json`, `.shp`, or `.gpkg` files are staged, and installs geomlint itself as part of the hook's own environment — nothing extra to install on your side beyond `pre-commit` itself.

## Any other CI system

There's no dependency on GitHub Actions specifically — the underlying contract is just a `pip install` and an exit code:

```bash
pip install geomlint
geomlint check ./data --fail-on error
```

Exit code `0` means clean, `1` means something at or above `--fail-on` was found — see [Exit codes](cli.md#exit-codes) for the full table, including the `2` usage-error case.
