"""Issue model and report rendering — table for humans, JSON for pipelines."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, replace
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    def rank(self) -> int:
        return {"error": 2, "warning": 1, "info": 0}[self.value]


@dataclass
class Issue:
    file: str
    feature_id: str
    severity: Severity
    code: str
    message: str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


def filter_at_or_above(issues: list[Issue], floor: Severity) -> list[Issue]:
    return [i for i in issues if i.severity.rank() >= floor.rank()]


def apply_config(issues: list[Issue], config) -> list[Issue]:
    """Drop disabled-check issues and remap severity per config overrides."""
    out = []
    for issue in issues:
        if not config.is_enabled(issue.code):
            continue
        override = config.severity_overrides.get(issue.code)
        if override:
            issue = replace(issue, severity=Severity(override))
        out.append(issue)
    return out


def render_table(issues: list[Issue]) -> str:
    if not issues:
        return "No issues found. ✓"

    rows = []
    widths = {"severity": 8, "code": 20, "file": 28, "feature_id": 12}
    for i in issues:
        rows.append(
            (
                i.severity.value.upper(),
                i.code,
                _truncate(i.file, widths["file"]),
                _truncate(i.feature_id, widths["feature_id"]),
                i.message,
            )
        )

    header = f"{'SEVERITY':<8} {'CODE':<20} {'FILE':<28} {'FEATURE':<12} MESSAGE"
    lines = [header, "-" * len(header)]
    for sev, code, file, fid, msg in rows:
        lines.append(f"{sev:<8} {code:<20} {file:<28} {fid:<12} {msg}")

    counts = {}
    for i in issues:
        counts[i.severity.value] = counts.get(i.severity.value, 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    lines.append("")
    lines.append(f"{len(issues)} issue(s) — {summary}")
    return "\n".join(lines)


def render_json(issues: list[Issue]) -> str:
    return json.dumps([i.to_dict() for i in issues], indent=2)


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"
