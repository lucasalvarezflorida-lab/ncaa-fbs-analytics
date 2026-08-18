"""Margin -> win-probability curves fitted on historical residuals.

Two curves live in margin_prob_curve.json (built by fit_margin_curve.py):

  model   residuals of actual margin vs THIS model's margin (prior-year final
          FPI gap + 2.5 HFA). Converts a model margin to a win probability.
  market  residuals of actual margin vs the closing spread. Converts a market
          spread to the market's own implied win probability — the fallback
          when no moneyline is posted.

win_prob is a Gaussian-kernel-smoothed empirical CDF of the residuals, so the
true sigma, skew, and tail weight come from the data instead of the Season
Sim's Normal(0, 13.5) assumption. The two curves differ because the market's
prediction is sharper than the model's — the model curve is wider.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.special import ndtr

HERE = Path(__file__).resolve().parent
CURVE_JSON = HERE / "margin_prob_curve.json"


class MarginCurve:
    def __init__(self, residuals, bandwidth: float, meta: dict | None = None):
        self.residuals = np.sort(np.asarray(residuals, dtype=float))
        self.bandwidth = float(bandwidth)
        self.meta = meta or {}

    @classmethod
    def fit(cls, residuals, meta: dict | None = None) -> "MarginCurve":
        r = np.asarray(residuals, dtype=float)
        bw = 1.06 * r.std() * len(r) ** -0.2  # Silverman's rule
        full_meta = dict(meta or {})
        full_meta.update(n=int(len(r)), resid_mean=round(float(r.mean()), 3),
                         resid_sd=round(float(r.std()), 3),
                         bandwidth=round(float(bw), 3))
        return cls(r, bw, full_meta)

    def win_prob(self, margin):
        """P(actual margin > 0 | predicted margin). Scalar in, scalar out;
        array in, array out."""
        m = np.atleast_1d(np.asarray(margin, dtype=float))
        p = ndtr((m[:, None] + self.residuals[None, :])
                 / self.bandwidth).mean(axis=1)
        return float(p[0]) if np.ndim(margin) == 0 else p

    def to_dict(self) -> dict:
        return dict(residuals=[round(float(x), 2) for x in self.residuals],
                    bandwidth=self.bandwidth, meta=self.meta)

    @classmethod
    def from_dict(cls, d: dict) -> "MarginCurve":
        return cls(d["residuals"], d["bandwidth"], d.get("meta"))


def save_curves(curves: dict[str, MarginCurve], path: Path = CURVE_JSON) -> None:
    payload = {name: c.to_dict() for name, c in curves.items()}
    Path(path).write_text(json.dumps(payload), encoding="utf-8")


def load_curve(name: str = "model", path: Path = CURVE_JSON) -> MarginCurve:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"{p} not found — run fit_margin_curve.py once to build it")
    return MarginCurve.from_dict(json.loads(p.read_text(encoding="utf-8"))[name])
