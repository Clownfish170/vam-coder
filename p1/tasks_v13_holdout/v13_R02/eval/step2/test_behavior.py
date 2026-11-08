import math
import pytest
from layout import scaled_areas
from shapes import Circle, Rect


def test_scaled_areas():
    items = [Circle(1), Rect(2, 3)]
    out = scaled_areas(items, 2)
    assert len(out) == 2
    assert abs(out[0] - math.pi * 4) < 1e-6
    assert out[1] == 24


def test_invalid_factor_propagates():
    with pytest.raises(ValueError):
        scaled_areas([Circle(1)], 0)


def test_scale_contract_regression():
    with pytest.raises(ValueError):
        Circle(1).scale(-2)
