import pytest
from charges import apply_fee
from tiers import BASE_FEE


def test_default_fee_uses_base():
    assert apply_fee(100) == 100 + BASE_FEE


def test_explicit_fee_unchanged():
    assert apply_fee(100, 5) == 105
