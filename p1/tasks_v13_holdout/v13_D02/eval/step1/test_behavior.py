from parserx import normalize


def test_strip_and_lower():
    assert normalize("  Ab C  ") == "ab c"


def test_squeeze_still_works():
    assert normalize("a  b") == "a b"
