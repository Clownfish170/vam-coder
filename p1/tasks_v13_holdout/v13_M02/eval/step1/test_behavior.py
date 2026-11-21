from stream import dedupe


def test_order_preserved():
    assert dedupe(["b", "a", "b", "c"]) == ["b", "a", "c"]


def test_numeric_input():
    assert dedupe([1, 1, 2]) == [1, 2]
