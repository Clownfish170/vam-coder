import alpha, beta


def test_a():
    assert alpha.a() == 10


def test_b_untouched():
    assert beta.b() == 2
