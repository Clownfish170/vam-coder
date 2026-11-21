import guard


def test_safe_ok():
    assert guard.is_safe("cmd:a=1;b=2") is True


def test_safe_empty_payload():
    assert guard.is_safe("cmd:") is False


def test_safe_bad_field():
    assert guard.is_safe("cmd:oops") is False
