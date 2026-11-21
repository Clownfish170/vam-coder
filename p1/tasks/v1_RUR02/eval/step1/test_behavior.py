import hot, stable_a, stable_b


def test_hot():
    assert hot.hot() == 2


def test_stable():
    assert stable_a.fa() == 'A' and stable_b.fb() == 'B'
