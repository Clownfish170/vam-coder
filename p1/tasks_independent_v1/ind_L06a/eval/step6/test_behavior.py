import verify


def test_check_v1():
    assert verify.check("hi|there") is True


def test_check_v2():
    assert verify.check("v2|login|alice|urgent") is True


def test_check_bad():
    assert verify.check("lonely") is False


def test_kind_regression():
    assert verify.kind_of("hi|there") == "hi"
