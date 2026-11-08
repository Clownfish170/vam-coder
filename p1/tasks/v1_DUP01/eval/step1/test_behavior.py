import mathx, textx


def test_mathx():
    assert mathx.norm(8) == 2


def test_textx():
    assert textx.norm(' a ') == 'a'
