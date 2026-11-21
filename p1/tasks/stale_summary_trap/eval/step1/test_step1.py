import pricing


def test_unit_updated():
    assert pricing.UNIT == 12


def test_price_uses_new_unit():
    assert pricing.price(3) == 36


def test_docstring_unchanged():
    # v0.2：step1 禁止顺手改 docstring，排除过期摘要混淆
    import inspect

    doc = inspect.getdoc(pricing.price) or ""
    assert "(=10)" in doc, f"docstring must stay frozen, got: {doc!r}"
