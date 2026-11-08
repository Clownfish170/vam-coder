import pytest

import shipping


def test_negative_weight():
    with pytest.raises(ValueError):
        shipping.weight_fee(-1)


def test_quote_negative():
    with pytest.raises(ValueError):
        shipping.quote(100, -2, 10)


def test_free_regression():
    assert shipping.quote(600, 10, 10) == 60.0
