import verify


def test_check_ok():
    assert verify.check("hi|there") is True


def test_check_bad():
    assert verify.check("lonely") is False


def test_kind_regression():
    assert verify.kind_of("hi|there") == "hi"
