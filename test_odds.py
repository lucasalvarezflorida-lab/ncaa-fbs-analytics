"""pytest suite for odds.py — run: pytest test_odds.py"""

import math

import pytest

from odds import american_to_prob, kelly, novig, overround, prob_to_american


def test_american_to_prob():
    assert math.isclose(american_to_prob(-110), 110 / 210)
    assert math.isclose(american_to_prob(150), 0.4)
    assert math.isclose(american_to_prob(100), 0.5)
    assert math.isclose(american_to_prob(-100), 0.5)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        american_to_prob(50)
    with pytest.raises(ValueError):
        prob_to_american(0.0)
    with pytest.raises(ValueError):
        prob_to_american(1.0)
    with pytest.raises(ValueError):
        novig(-110, -110, "banana")


def test_prob_to_american_round_trip():
    for ml in (-450, -200, -110, 100, 120, 285, 900):
        assert prob_to_american(american_to_prob(ml)) == ml


def test_overround():
    assert math.isclose(overround(-110, -110), 220 / 210 - 1)


def test_novig_even_market():
    for method in ("proportional", "power", "shin"):
        pa, pb = novig(-110, -110, method)
        assert math.isclose(pa, 0.5, abs_tol=1e-6), method
        assert math.isclose(pa + pb, 1.0, abs_tol=1e-9), method


def test_novig_sums_to_one():
    for method in ("proportional", "power", "shin"):
        pa, pb = novig(-450, 340, method)
        assert math.isclose(pa + pb, 1.0, abs_tol=1e-9), method
        assert pa > 0.5 > pb, method


def test_kelly():
    assert kelly(0.5, 100) == 0.0                      # exactly break-even
    assert math.isclose(kelly(0.6, 100), 0.2)          # (0.6-0.5)/(1-0.5)
    assert math.isclose(kelly(0.6, 100, 0.25), 0.05)   # quarter-Kelly
    assert kelly(0.2, 150) == 0.0                      # -EV price -> no bet
    # b = 2.65 at +265: f = p - (1-p)/b
    assert math.isclose(kelly(0.57, 265), 0.57 - 0.43 / 2.65)
    with pytest.raises(ValueError):
        kelly(1.0, -110)


def test_longshot_shading():
    # power and shin give the favorite at least the proportional share:
    # they model the vig as concentrated on the longshot
    prop_fav, prop_dog = novig(-450, 340, "proportional")
    for method in ("power", "shin"):
        fav, dog = novig(-450, 340, method)
        assert fav >= prop_fav - 1e-12, method
        assert dog <= prop_dog + 1e-12, method
