import core


def test_compute_double_exists():
    assert hasattr(core, "compute_double")
    assert core.compute_double(3) == 6


def test_old_name_gone():
    assert not hasattr(core, "compute")


def test_helper_updated():
    assert core.helper(3) == 7


def test_caller_updated():
    import app

    assert app.run(3) == 7
