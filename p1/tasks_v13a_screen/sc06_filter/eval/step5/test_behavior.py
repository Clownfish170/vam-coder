def test():
    from main import bounded
    assert bounded(0) == -1
    assert bounded(100) == 50
