def test():
    from main import bounded
    assert bounded(0) == 0
    assert bounded(100) == 50
