"""Totals model - SHADOW (Phase 2, built 2026-09-22).

The on-air machine predicts a margin and lays it over a guessed total. This
projects the total itself: PACE times POINTS PER PLAY.

  pace   plays_obs_i = mu_plays + pace_i + opp_pace_j (+ e), ridge with prior 0
         on both, LAM_PACE games of evidence -> predicted plays for each side.
  ppp    expected points for offense i against defense j at league pace
         = mu_pts + off_i - def_j + HFA*home, with off / def from the Phase 1
         efficiency solve (efficiency_ratings.solve, "eff") or from a plain
         points-for / points-against ridge on actual points ("pts", the
         baseline); divided by mu_plays it is points per play.
  total  = plays_h * ppp_h + plays_a * ppp_a;  margin2 = plays_h*ppp_h - plays_a*ppp_a
An optional calibration (a + b * total) is fit on the fit seasons only.

    python totals_model.py --backtest                 # 2022-2026 vs the closing total (internal)
    python totals_model.py --backtest --tune          # lam grid, fit 2022-24 / test 2025
    python totals_model.py --week 4                   # shadow totals + shadow score calls for the card
Writes internal/shadow_totals_week{N}.json and puts a `machine_shadow` score
call (the on-air margin laid over the modeled total) into score_tracker.json
next to the on-air call. SHADOW: never a slide, never the on-air call, until
Lucas switches it. Closing totals are market material - internal only."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
import efficiency_ratings as er  # noqa: E402

LAM_PACE = 3.0
LAM_PTS = 3.0
HFA = 2.5
MU_PLAYS0, MU_PTS0 = 66.0, 26.5      # league constants before any game (2022-25 means 66.6 / 26.1-27.0)


def pace_solve(teams: list[str], obs: list[dict], lam: float = LAM_PACE):
    """{team: (pace, opp_pace)} deviations from mu_plays, plus mu_plays."""
    idx = {t: i for i, t in enumerate(teams)}
    m = len(teams)
    obs = [o for o in obs if o["off"] in idx and o["def_"] in idx]
    if not obs or not np.isfinite(lam):
        return {t: (0.0, 0.0) for t in teams}, MU_PLAYS0
    y = np.array([o["plays"] for o in obs], dtype=float)
    mu = float(y.mean())
    X = np.zeros((len(obs), 2 * m))
    X[np.arange(len(obs)), [idx[o["off"]] for o in obs]] = 1.0
    X[np.arange(len(obs)), [m + idx[o["def_"]] for o in obs]] = 1.0
    d = np.linalg.solve(X.T @ X + lam * np.eye(2 * m), X.T @ (y - mu))
    return {t: (float(d[i]), float(d[m + i])) for t, i in idx.items()}, mu


def pts_solve(prior: dict[str, float], obs: list[dict], lam: float = LAM_PTS, hfa: float = HFA):
    """Baseline: actual points scored per side, ridge with FPI/2 as the prior on
    offense and defense. Same shape as efficiency_ratings.solve."""
    fake = [dict(o, D=o["pts"]) for o in obs]
    return er.solve(prior, fake, lam=lam, lam_st=1e9, hfa=hfa, scale=1.0)


class TotalsModel:
    def __init__(self, source="eff", lam_pace=LAM_PACE, lam_pts=LAM_PTS, lam_eff=er.LAM, hfa=HFA, calib=None, desc=""):
        self.source, self.lam_pace, self.lam_pts, self.lam_eff, self.hfa = source, lam_pace, lam_pts, lam_eff, hfa
        self.calib = calib        # (a, b) or None
        self.desc = desc or f"{source} totals: lam_pace {lam_pace:g}, lam {lam_eff if source == 'eff' else lam_pts:g}"
        self._obs = {}

    def obs(self, season):
        if season not in self._obs:
            self._obs[season] = er.load_obs(season)
        return self._obs[season]

    def fit_week(self, prior: dict, teams: list, obs_before: list[dict]):
        pace, mu_plays = pace_solve(teams, obs_before, self.lam_pace)
        if self.source == "eff":
            units = er.solve(prior, obs_before, lam=self.lam_eff, lam_st=1e9, hfa=self.hfa)
        else:
            units = pts_solve(prior, obs_before, self.lam_pts, self.hfa)
        mu_pts = float(np.mean([o["pts"] for o in obs_before])) if obs_before else MU_PTS0
        return dict(pace=pace, mu_plays=mu_plays, units=units, mu_pts=mu_pts)

    def predict(self, fit: dict, home: str, away: str, neutral: bool):
        """(total, margin, pts_home, pts_away, plays_home, plays_away)."""
        u, pc = fit["units"], fit["pace"]
        plays_h = fit["mu_plays"] + pc[home][0] + pc[away][1]
        plays_a = fit["mu_plays"] + pc[away][0] + pc[home][1]
        h = 0.0 if neutral else self.hfa
        ppp_h = (fit["mu_pts"] + u[home]["off"] - u[away]["def_"] + h) / fit["mu_plays"]
        ppp_a = (fit["mu_pts"] + u[away]["off"] - u[home]["def_"]) / fit["mu_plays"]
        ph, pa = max(plays_h * ppp_h, 3.0), max(plays_a * ppp_a, 3.0)
        total = ph + pa
        if self.calib:
            total = self.calib[0] + self.calib[1] * total
        return total, ph - pa, ph, pa, plays_h, plays_a


# ---------------- backtest vs the closing total ----------------

def season_rows(season: int, model: TotalsModel, ctx=None, weeks=range(1, 16)) -> list[dict]:
    import backtest as bt
    ctx = ctx or bt.SeasonCtx(season)
    obs = model.obs(season)
    out = []
    for w in weeks:
        games = [g for g in ctx.games if g["week"] == w]
        if not games:
            continue
        fit = model.fit_week(ctx.prior, ctx.teams, [o for o in obs if o["week"] < w])
        avg_total = 2 * fit["mu_pts"]
        for g in games:
            t, m2, ph, pa, plh, pla = model.predict(fit, g["home"], g["away"], g["neutral"])
            ln = ctx.lines.get(g["id"], {})
            out.append(dict(id=g["id"], season=season, wk=w, home=g["home_raw"], away=g["away_raw"], total=g["total"],
                            margin=g["margin"], pred=t, margin2=m2, pts_h=ph, pts_a=pa, plays_h=plh, plays_a=pla,
                            avg=avg_total, ou=ln.get("ou")))
    return out


def score(rows: list[dict], key="pred") -> dict:
    R = [r for r in rows if r.get("ou") is not None]
    if not R:
        return dict(n=0)
    e = np.array([r["total"] - r[key] for r in R]); ek = np.array([r["total"] - r["ou"] for r in R])
    ea = np.array([r["total"] - r["avg"] for r in R])
    d = np.array([r[key] - r["ou"] for r in R]); live = np.abs(d) >= 1.0
    res = ek[live] * np.sign(d[live])
    out = dict(n=len(R), mae=float(np.mean(np.abs(e))), bias=float(np.mean(e)), rmse=float(np.sqrt(np.mean(e ** 2))),
               mae_close=float(np.mean(np.abs(ek))), mae_avg=float(np.mean(np.abs(ea))),
               dist_close=float(np.mean(np.abs(d))),
               closer=int(np.sum(np.abs(e) < np.abs(ek))), farther=int(np.sum(np.abs(e) > np.abs(ek))),
               ou_w=int(np.sum(res > 0)), ou_l=int(np.sum(res < 0)), ou_p=int(np.sum(res == 0)))
    out["ou_pct"] = out["ou_w"] / max(out["ou_w"] + out["ou_l"], 1)
    # the totals model's own margin, for the record
    em = np.array([r["margin"] - r["margin2"] for r in R])
    out["margin2_mae"] = float(np.mean(np.abs(em)))
    return out


def calibrate(rows: list[dict]) -> tuple[float, float]:
    R = [r for r in rows if r["wk"] >= 2]
    x = np.array([r["pred"] for r in R]); y = np.array([r["total"] for r in R])
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def fmt(name, s):
    if not s.get("n"):
        return f"{name:26s} -"
    return (f"{name:26s} {s['n']:5d} {s['mae']:6.2f} {s['rmse']:6.2f} {s['bias']:+6.2f} | close {s['mae_close']:6.2f} avg {s['mae_avg']:6.2f}"
            f" | closer {s['closer']}-{s['farther']} | O/U vs close {s['ou_w']}-{s['ou_l']}-{s['ou_p']} ({100 * s['ou_pct']:.1f}%) | margin2 MAE {s['margin2_mae']:.2f}")


def run_backtest(seasons, tune=False, out_json=None):
    import backtest as bt
    ctxs = {s: bt.SeasonCtx(s) for s in seasons}
    fit_s = [s for s in seasons if s <= 2024]; test_s = [s for s in seasons if s == 2025]
    report = dict(generated=dt.datetime.now().isoformat(timespec="seconds"), seasons=seasons, models={})
    models = {"eff": TotalsModel("eff"), "pts": TotalsModel("pts")}
    print(f"{'model':26s} {'n':>5} {'MAE':>6} {'RMSE':>6} {'bias':>6} | closing total | league avg | closer | O/U vs close (>=1 apart)")
    for name, model in models.items():
        rows = {s: season_rows(s, model, ctxs[s]) for s in seasons}
        cal = calibrate([r for s in fit_s for r in rows[s]]) if fit_s else (0.0, 1.0)
        rows_c = {s: [dict(r, pred=cal[0] + cal[1] * r["pred"]) for r in rows[s]] for s in seasons}
        rep = dict(desc=model.desc, calib=cal, seasons={}, seasons_cal={})
        print(f"\n=== {name}: {model.desc} | calibration fit on {fit_s}: total = {cal[0]:.2f} + {cal[1]:.3f} * raw ===")
        for s in seasons:
            rep["seasons"][s] = score(rows[s]); rep["seasons_cal"][s] = score(rows_c[s])
            print(fmt(f"{s} raw", rep["seasons"][s]))
            print(fmt(f"{s} calibrated", rep["seasons_cal"][s]))
        pooled = [r for s in seasons for r in rows[s]]; pooled_c = [r for s in seasons for r in rows_c[s]]
        rep["pooled"], rep["pooled_cal"] = score(pooled), score(pooled_c)
        print(fmt("POOLED raw", rep["pooled"])); print(fmt("POOLED calibrated", rep["pooled_cal"]))
        rep["by_week"] = {}
        for w in range(1, 16):
            W = [r for r in pooled_c if r["wk"] == w and r.get("ou") is not None]
            if W:
                rep["by_week"][w] = dict(n=len(W), mae=float(np.mean([abs(r["total"] - r["pred"]) for r in W])),
                                         close=float(np.mean([abs(r["total"] - r["ou"]) for r in W])))
        print("  by week (calibrated MAE / closing):", " ".join(f"wk{w}:{v['mae']:.1f}/{v['close']:.1f}" for w, v in rep["by_week"].items()))
        # by size of the closing total
        rep["by_total"] = []
        for lo, hi in ((0, 44.5), (45, 52.5), (53, 60.5), (61, 200)):
            W = [r for r in pooled_c if r.get("ou") is not None and lo <= r["ou"] <= hi]
            if W:
                d = dict(bucket=f"{lo:g}-{hi:g}", n=len(W), mae=float(np.mean([abs(r["total"] - r["pred"]) for r in W])),
                         close=float(np.mean([abs(r["total"] - r["ou"]) for r in W])),
                         over=int(sum(r["total"] > r["ou"] for r in W)), under=int(sum(r["total"] < r["ou"] for r in W)))
                rep["by_total"].append(d)
        print("  by closing total (calibrated MAE / closing, overs-unders):",
              " ".join(f"{d['bucket']}: {d['mae']:.1f}/{d['close']:.1f} {d['over']}-{d['under']}" for d in rep["by_total"]))
        report["models"][name] = rep
    if tune and fit_s and test_s:
        print(f"\n=== TUNE totals: fit {fit_s} / test {test_s} (calibrated on fit) ===")
        res = []
        for src in ("eff", "pts"):
            for lp in (1, 3, 6, 12, float("inf")):
                for lu in (2, 3, 5):
                    m = TotalsModel(src, lam_pace=lp, lam_eff=lu, lam_pts=lu)
                    rows = {s: season_rows(s, m, ctxs[s]) for s in seasons}
                    cal = calibrate([r for s in fit_s for r in rows[s]])
                    rc = {s: [dict(r, pred=cal[0] + cal[1] * r["pred"]) for r in rows[s]] for s in seasons}
                    f = score([r for s in fit_s for r in rc[s]]); t = score([r for s in test_s for r in rc[s]])
                    res.append(dict(source=src, lam_pace=lp, lam_units=lu, calib=cal, fit_mae=f["mae"], fit_ou=f["ou_pct"],
                                    test_mae=t["mae"], test_ou=t["ou_pct"], test_close=t["mae_close"]))
        res.sort(key=lambda r: r["fit_mae"])
        report["tune"] = res
        print(f"{'src':>4} {'lam_pace':>8} {'lam_u':>5} | {'fit MAE':>8} {'O/U':>6} | {'test MAE':>8} {'O/U':>6} {'close':>6}")
        for r in res[:12]:
            print(f"{r['source']:>4} {r['lam_pace']:8g} {r['lam_units']:5g} | {r['fit_mae']:8.3f} {100 * r['fit_ou']:5.1f}% | {r['test_mae']:8.3f} {100 * r['test_ou']:5.1f}% {r['test_close']:6.2f}")
    if out_json:
        Path(out_json).write_text(json.dumps(report, indent=1, default=float), encoding="utf-8")
        print("wrote", out_json)
    return report


# ---------------- 2026 weekly shadow ----------------

def shadow_week(week: int, calib=None, write=True) -> dict:
    import backtest as bt
    from freeze_card import score_call
    ctx = bt.SeasonCtx(2026)
    model = TotalsModel("eff", calib=calib)
    obs = er.load_obs(2026, ctx.games, rebuild=True)
    fit = model.fit_week(ctx.prior, ctx.teams, [o for o in obs if o["week"] < week])
    src = HERE / f"card_data_week{week}_frozen.json"
    if not src.exists():
        src = HERE / f"card_data_week{week}.json"
    card = {(g["away"], g["home"]): g for g in json.loads(src.read_text(encoding="utf-8"))["games"]}
    from name_mapping import normalize_name as nn
    games = []
    for (a, h), g in card.items():
        na, nh = nn(a), nn(h)
        if na not in fit["units"] or nh not in fit["units"]:
            continue
        t, m2, ph, pa, plh, pla = model.predict(fit, nh, na, bool(g.get("neutral")))
        games.append(dict(game_id=g["game_id"], away=a, home=h, shadow_total=round(t, 1), shadow_pts=[round(pa, 1), round(ph, 1)],
                          shadow_plays=[round(pla, 1), round(plh, 1)], model_margin=g["model_margin"],
                          machine_call_on_air=(score_call(g["model_margin"], float(g["ou"])) if g.get("ou") is not None else None),
                          machine_shadow=score_call(g["model_margin"], t)))
    out = dict(week=week, as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), status="SHADOW - not on air",
               params=dict(lam_pace=model.lam_pace, lam_eff=model.lam_eff, hfa=model.hfa, calib=calib, mu_plays=round(fit["mu_plays"], 1),
                           mu_pts=round(fit["mu_pts"], 2)), games=games)
    if write:
        (HERE / "internal").mkdir(exist_ok=True)
        (HERE / "internal" / f"shadow_totals_week{week}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
        # score_tracker: the on-air margin laid over the SHADOW total, beside the on-air call
        st_path = HERE / "score_tracker.json"
        rows = json.loads(st_path.read_text(encoding="utf-8"))
        by = {(g["away"], g["home"]): g for g in games}
        n = 0
        for r in rows:
            g = by.get((r["away"], r["home"]))
            if g and r["week"] == week:
                r["machine_shadow"] = g["machine_shadow"]; r["shadow_total"] = g["shadow_total"]; n += 1
        st_path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print(f"score_tracker.json: machine_shadow written on {n} week-{week} rows")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--seasons", default="2022-2026")
    ap.add_argument("--week", type=int)
    ap.add_argument("--calib", default="", help="a,b calibration for the shadow total (from the backtest)")
    a = ap.parse_args()
    if a.backtest:
        lo, _, hi = a.seasons.partition("-")
        run_backtest(list(range(int(lo), int(hi or lo) + 1)), tune=a.tune, out_json=str(HERE / "internal" / "backtest_totals.json"))
    if a.week:
        cal = tuple(float(x) for x in a.calib.split(",")) if a.calib else None
        out = shadow_week(a.week, cal)
        print(f"SHADOW totals before week {a.week} (mu plays {out['params']['mu_plays']}, mu pts {out['params']['mu_pts']}) - not on air")
        for g in out["games"]:
            print(f"  {g['away']} at {g['home']:14s} shadow total {g['shadow_total']:5.1f}  plays {g['shadow_plays']}  "
                  f"shadow call (away-home) {g['machine_shadow']}  on-air call {g['machine_call_on_air']}")
        print(f"wrote internal/shadow_totals_week{a.week}.json")
