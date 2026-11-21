def test_margin():
    from config_consts import MARGIN
    assert abs(MARGIN - 0.20) < 1e-9
