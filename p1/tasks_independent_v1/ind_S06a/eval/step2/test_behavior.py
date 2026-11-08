import expand


def test_pad_right():
    assert expand.pad_right("7", 3, "0") == "700"


def test_pad_right_dots():
    assert expand.pad_right("hi", 5, ".") == "hi..."


def test_pad_left_regression():
    assert expand.pad_left("7", 3, "0") == "007"
