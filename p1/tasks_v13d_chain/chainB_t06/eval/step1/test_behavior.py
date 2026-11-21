def test():
    from dispatch import fallback
    assert fallback() == 'backup!'
