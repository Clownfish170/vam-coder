import hot, stable_a, stable_b


def test_hot3():
    assert hot.hot() == 3


def test_stable():
    assert stable_a.fa() == 'A' and stable_b.fb() == 'B'
