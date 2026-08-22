"""Positional drift / GPS multipath detection — NOT YET IMPLEMENTED.

This is the hard, genuinely research-y half of the observability gap: telling
a real turn from a multipath-induced jump requires a speed/heading-plausibility
model, not just a distance threshold, or every sharp legitimate turn in a
parking lot trips the same alarm as a reflected signal off a building.

Deliberately shipping this as a stub rather than a fake "distance > threshold"
check that would just be noise. Roadmap, in order:

  1. Require features to carry a track/device id + timestamp (most vector
     formats don't guarantee either — this alone will kill half of real-world
     inputs and needs a clear error message, not a silent skip).
  2. Compute implied speed between consecutive fixes per track; flag jumps
     that exceed a plausible speed envelope for the declared mode of travel.
  3. Layer in heading-change-without-corresponding-speed-drop as a second
     signal — real turns slow down, multipath teleports don't.
  4. Validate against a labeled dataset before trusting it on anything real —
     see the open GNSS multipath research this leans on (u-blox/Septentrio
     application notes, academic multipath-analysis tooling) before assuming
     any of the above thresholds are right.

Called from the CLI behind --drift; today it always raises so nobody
mistakes silence for "checked and clean."
"""

from __future__ import annotations


class DriftCheckNotImplemented(NotImplementedError):
    pass


def check_drift(*_args, **_kwargs):
    raise DriftCheckNotImplemented(
        "drift detection is not implemented yet (see geomlint/checks/drift.py "
        "for the roadmap) — omit --drift, this is not a silent no-op"
    )
