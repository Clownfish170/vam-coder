import codec


def test_negotiate_fallback():
    assert codec.negotiate([3, 4]) == 1


def test_negotiate_common_regression():
    assert codec.negotiate([1, 2]) == 2
    assert codec.negotiate([2]) == 2


def test_version_regression():
    assert codec.version_of("v2|a|b|c") == 2
