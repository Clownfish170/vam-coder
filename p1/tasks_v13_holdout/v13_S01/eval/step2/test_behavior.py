import backoff


def test_cap_half():
    assert backoff.cap_half(10) == 5
    assert backoff.cap_half(5) == 2


def test_delay_regression():
    assert backoff.delay(2, 5) == 30
