"""American-odds helpers: implied probability, fair odds, two-sided devig.

Stdlib only, so anything in the repo can import it without ceremony.
market-postmortem/pm_common.py keeps its own american_return (profit per $1);
these are the probability-space counterparts.
"""

from __future__ import annotations


def american_to_prob(ml: float) -> float:
    """Implied probability of American odds, vig included.

    >>> round(american_to_prob(-110), 4)
    0.5238
    >>> american_to_prob(150)
    0.4
    """
    ml = float(ml)
    if -100 < ml < 100:
        raise ValueError(f"American odds must be <= -100 or >= +100, got {ml}")
    return -ml / (-ml + 100) if ml < 0 else 100 / (ml + 100)


def prob_to_american(p: float) -> int:
    """Fair (no-vig) American odds for a win probability. 0.5 -> +100.

    >>> prob_to_american(0.6)
    -150
    >>> prob_to_american(0.25)
    300
    """
    if not 0.0 < p < 1.0:
        raise ValueError(f"probability must be in (0, 1), got {p}")
    if p > 0.5:
        return -round(100 * p / (1 - p))
    return round(100 * (1 - p) / p)


def overround(ml_a: float, ml_b: float) -> float:
    """The book's margin: total implied probability minus 1."""
    return american_to_prob(ml_a) + american_to_prob(ml_b) - 1


def novig(ml_a: float, ml_b: float,
          method: str = "proportional") -> tuple[float, float]:
    """No-vig probabilities (p_a, p_b) from a two-sided market.

    proportional  q_i / sum(q) — assumes the vig is applied evenly
    power         q_i ** k with k solved so probabilities sum to 1
    shin          Shin (1992) insider-trading model
    Power and shin both put more of the vig on the longshot, matching the
    favorite-longshot bias (books shade dogs, so proportional overstates the
    dog's fair probability on lopsided lines).
    """
    qa, qb = american_to_prob(ml_a), american_to_prob(ml_b)
    s = qa + qb
    if method == "proportional":
        return qa / s, qb / s
    if method == "power":
        # sum(q**k) is monotone decreasing in k; booked sum > 1 so k > 1
        lo, hi = 1.0, 100.0
        for _ in range(100):
            k = (lo + hi) / 2
            if qa ** k + qb ** k > 1.0:
                lo = k
            else:
                hi = k
        pa, pb = qa ** k, qb ** k
        return pa / (pa + pb), pb / (pa + pb)
    if method == "shin":
        # two-outcome Shin: find z with sum(p_i(z)) == 1 (monotone in z)
        def probs(z):
            return tuple((( (z * z + 4 * (1 - z) * q * q / s) ** 0.5 ) - z)
                         / (2 * (1 - z)) for q in (qa, qb))
        lo, hi = 0.0, 0.5
        for _ in range(100):
            z = (lo + hi) / 2
            if sum(probs(z)) > 1.0:
                lo = z
            else:
                hi = z
        pa, pb = probs((lo + hi) / 2)
        return pa / (pa + pb), pb / (pa + pb)
    raise ValueError(f"unknown devig method: {method!r}")
