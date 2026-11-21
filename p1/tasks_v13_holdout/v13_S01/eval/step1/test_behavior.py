import backoff


def test_cap_when_many_attempts():
    assert backoff.delay(2, 5) == 30
    assert backoff.delay(3, 7) == 30


def test_normal_exponential():
    assert backoff.delay(2, 3) == 16
    assert backoff.delay(1, 0) == 1


def test_full_delay_regression():
    assert backoff.full_delay(2, 9) == 30
