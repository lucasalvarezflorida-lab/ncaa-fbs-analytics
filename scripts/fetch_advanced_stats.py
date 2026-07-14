"""
DEPRECATED — replaced by fetch_sp_plus.py.

Previously fetched EPA-per-play, success rate, and explosiveness from
CFBD's /stats/season/advanced endpoint and normalized them via min-max
scaling. Both the methodology (re-deriving an opponent-adjusted rating
when SP+ already exists) and the normalization (min-max anchored to
yearly extremes) are superseded.

See the README for the rationale.
"""

raise RuntimeError(
    "fetch_advanced_stats.py is deprecated. Use fetch_sp_plus.py instead."
)
