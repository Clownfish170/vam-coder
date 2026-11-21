import expand


def test_pad():
    assert expand.pad_left("7", 3, "0") == "007"


def test_pad_dots():
    assert expand.pad_left("hi", 5, ".") == "...hi"


def test_no_pad_needed():
    assert expand.pad_left("hello", 3, "0") == "hello"
