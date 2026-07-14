"""
DEPRECATED — replaced by fetch_sp_plus.py.

The earlier methodology built our own opponent-adjusted points rating
to blend with EPA at a 75/25 ratio. The blend ratio was inherited from
the NHL model's backtest-tuned weights with no defensible reason to be
that ratio for football. The rewrite (May 2026) replaced the blend with
Bill Connelly's SP+ as the base — opponent-adjusted by construction,
publicly available via CFBD, and peer-reviewed.

This file is kept as a stub for historical reference. Do not run it.
"""

raise RuntimeError(
    "fetch_team_ratings.py is deprecated. Use fetch_sp_plus.py instead. "
    "See README §'Why lift SP+ rather than recompute our own blend'."
)
