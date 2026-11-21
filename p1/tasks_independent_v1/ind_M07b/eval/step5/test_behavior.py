import flow


def test_new_default():
    assert flow.default_flow() == ["read", "upper", "dedupe"]


def test_execute_with_new_default():
    out = flow.execute(["ab", "ab", "cd"])
    assert out == ["AB", "CD"]


def test_total_regression():
    assert flow.execute([2, 3], ["total"]) == [5]
