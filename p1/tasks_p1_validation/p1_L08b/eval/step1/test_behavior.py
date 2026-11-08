from leaf import render_n


def test_shape():
    assert render_n(-2) == -1
    assert render_n(3) == 9
    assert render_n(0) == 0
