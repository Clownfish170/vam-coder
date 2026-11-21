def test_clamp():
    from engine import clamp
    assert clamp(50) == 50
    assert clamp(200) == 100
    assert clamp(-5) == 0
