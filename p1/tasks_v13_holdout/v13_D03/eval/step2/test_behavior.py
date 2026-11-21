from charges import apply_fee, describe
from tiers import BASE_FEE, tier


def test_boundary_200_gold():
    assert tier(200) == "gold"


def test_just_below():
    assert tier(199.99) == "silver"


def test_default_fee_regression():
    assert apply_fee(10) == 10 + BASE_FEE


def test_describe_follows_tier():
    assert describe(200) == "gold"
