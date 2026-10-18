import discount
import pricing


def test_price_still_correct():
    assert pricing.price(3) == 36


def test_fast_price_exists_and_matches():
    assert hasattr(discount, "fast_price")
    for qty in (0, 1, 3, 10):
        assert discount.fast_price(qty) == pricing.price(qty)


def test_fast_price_hardcoded_current_unit():
    # 写死当前单价 12；若用过期假设 10 会得到 30
    assert discount.fast_price(3) == 36
    assert discount.fast_price(10) == 120


def test_total_unchanged():
    assert discount.total(3) == 36
