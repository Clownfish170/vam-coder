import pytest

import balance


def test_amount_nonpositive():
    with pytest.raises(ValueError):
        balance.withdraw(100, 0)
    with pytest.raises(ValueError):
        balance.withdraw(100, -5)


def test_ok():
    assert balance.withdraw(100, 30) == 70
