import core


def test_helper_offset_two():
    assert core.helper(3) == 8


def test_compute_double_unchanged():
    assert core.compute_double(4) == 8


def test_caller_reflects_helper():
    import app

    assert app.run(4) == 10  # helper(4) = 4*2 + 2
