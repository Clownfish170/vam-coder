def test():
    from dispatch import fallback
    assert fallback() == 2
