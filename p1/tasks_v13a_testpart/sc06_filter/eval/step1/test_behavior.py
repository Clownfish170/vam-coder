def test():
    from main import clamp
    assert clamp(-1) == 0
    assert clamp(100) == 10
