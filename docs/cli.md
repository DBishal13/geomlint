# CLI reference

```text
geomlint [-h] [--version] {check} ...
```

`--version` prints the installed version and exits.

## `geomlint check`

```text
geomlint check [-h] [--format {table,json}] [--fail-on {error,warning,info}]
                [--config PATH] [--drift]
                paths [paths ...]
```

| Argument | Meaning |
|---|---|
| `paths` | One or more files or directories to scan. Directories are recursed for `.geojson`, `.json`, `.shp`, and `.gpkg`. Duplicate files across multiple paths are only checked once. |
| `--format {table,json}` | Output format. `table` (default) is human-readable; `json` is a list of issue objects, for piping into another tool. |
| `--fail-on {error,warning,info}` | Exit non-zero if any issue at or above this severity is found. Default `error`. Set to `warning` for a stricter CI gate. |
| `--config PATH` | Path to a `.geomlint.toml` config file. If omitted, geomlint auto-discovers one — see [Configuration](configuration.md). An explicit path that doesn't exist is an error, not a silent fallback. |
| `--drift` | Attempt positional/GPS-drift detection. Not implemented yet — this always fails clearly with a pointer to the roadmap rather than silently doing nothing. |

## Exit codes

| Code | Meaning |
|---|---|
| `0` | No issue at or above `--fail-on` was found. |
| `1` | At least one issue at or above `--fail-on` was found — the normal "found something" outcome. |
| `2` | Usage problem: no matching files under the given path(s), a `--config` file that doesn't exist, a malformed config file, or (with `--drift`) the not-yet-implemented error. |

`0`/`1` is the pair a CI step should actually branch on; `2` means geomlint couldn't run the check at all, which is worth treating as a separate failure mode (e.g. a bad path in the pipeline config) rather than "issues found."

## Examples

```bash
geomlint check ./parcels                          # table output, human-readable
geomlint check a.geojson b.gpkg ./more_data/       # multiple files/dirs in one run
geomlint check ./parcels --format json             # for piping into another tool
geomlint check ./parcels --fail-on warning          # stricter CI gate
geomlint check ./parcels --config custom.toml
```
