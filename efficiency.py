"""Per-game efficiency layer for the in-season rating — the "deserved margin".

The ridge update (inseason_ratings.py) learns from score margins. Margins
carry turnover luck, special-teams scores and garbage time; per-play
efficiency carries less of it. CFBD's /stats/game/advanced gives each team
per game: total PPA (predicted points added, summed over its offensive
plays), success rate, explosiveness. From the home side,

    net_tppa = home offense totalPPA - away offense totalPPA
    net_sr   = home offense successRate - away offense successRate

and the deserved margin is a linear model of those, fit on 2021-24 (frozen
in efficiency_model.json by backtest_efficiency.py). The update then fits
    y = EFF_W * actual margin + (1 - EFF_W) * deserved margin
per game; games without both teams' efficiency rows fall back to the actual
margin. Nothing about the prior, lambda, HFA or the cap changes.

Coverage note: CFBD's advanced box scores start thin in 2021 (~55% of FBS
games) and are complete from 2022 on.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

MODEL_JSON = HERE / "efficiency_model.json"
FEATURES = ["net_tppa", "net_sr"]


def _pick(g, *names):
    for k in names:
        if g.get(k) is not None:
            return g[k]
    return None


def game_efficiency(season: int, refresh: bool = False) -> dict[int, dict]:
    """{game_id: {net_tppa, net_sr, net_ex, home, away}} from the home side,
    for regular-season games where BOTH teams have an advanced box score.
    Team names are normalized like the rest of the pipeline."""
    import cfbd_client as cfbd
    games = cfbd.get("/games", {"year": season, "seasonType": "regular"}, False)
    adv = cfbd.get("/stats/game/advanced", {"year": season, "seasonType": "regular"}, refresh)
    gi = {}
    for g in games:
        home, away = _pick(g, "homeTeam", "home_team"), _pick(g, "awayTeam", "away_team")
        if home and away:
            gi[_pick(g, "id")] = (home, away)
    sides: dict[int, dict] = {}
    for r in adv:
        gid = _pick(r, "gameId", "game_id")
        if gid not in gi:
            continue
        home, away = gi[gid]
        side = "home" if r["team"] == home else ("away" if r["team"] == away else None)
        o = r.get("offense") or {}
        if side is None or o.get("totalPPA") is None or o.get("successRate") is None:
            continue
        sides.setdefault(gid, {})[side] = dict(
            tppa=float(o["totalPPA"]), sr=float(o["successRate"]),
            ex=float(o.get("explosiveness") or 0.0), plays=int(o.get("plays") or 0))
    out = {}
    for gid, s in sides.items():
        if "home" not in s or "away" not in s:
            continue
        h, a = s["home"], s["away"]
        home, away = gi[gid]
        out[gid] = dict(net_tppa=h["tppa"] - a["tppa"], net_sr=h["sr"] - a["sr"],
                        net_ex=h["ex"] - a["ex"], plays=h["plays"] + a["plays"],
                        home=normalize_name(home), away=normalize_name(away))
    return out


def fit_model(margins, feats: list[dict]) -> dict:
    """Least-squares deserved-margin model: margin ~ intercept + FEATURES."""
    X = np.column_stack([np.ones(len(feats))] + [[f[k] for f in feats] for k in FEATURES])
    y = np.asarray(margins, dtype=float)
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    pred = X @ b
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    return dict(intercept=float(b[0]), **{k: float(v) for k, v in zip(FEATURES, b[1:])},
                r2=float(r2), rmse=float(np.sqrt(np.mean((y - pred) ** 2))), n=int(len(y)))


def deserved(feats: dict, model: dict) -> float:
    return model["intercept"] + sum(model[k] * feats[k] for k in FEATURES)


def load_model() -> dict | None:
    if MODEL_JSON.exists():
        return json.loads(MODEL_JSON.read_text(encoding="utf-8"))
    return None


def save_model(model: dict, note: str) -> None:
    MODEL_JSON.write_text(json.dumps(dict(model, features=FEATURES, note=note), indent=1),
                          encoding="utf-8")


def blend(margin: float, feats: dict | None, model: dict | None, w: float) -> float:
    """EFF_W-weighted mix of the actual margin and the deserved margin; the
    actual margin alone when either the game's efficiency or the model is
    missing, or w == 1."""
    if w >= 1.0 or feats is None or model is None:
        return float(margin)
    return w * float(margin) + (1.0 - w) * deserved(feats, model)
