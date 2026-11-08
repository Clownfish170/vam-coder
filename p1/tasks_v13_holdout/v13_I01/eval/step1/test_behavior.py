import engine
from curves_body import calibrate


def test_matches_calibrate_table():
    for t in range(0, 13):
        assert engine.quote(t) == calibrate(t)


def test_adjust_regression():
    assert engine.adjust(-5) == 0
