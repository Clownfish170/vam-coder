import engine
import cli


def test_new_name():
    assert engine.evaluate(3) == 7


def test_old_gone():
    assert not hasattr(engine, "compute")
    assert not hasattr(cli, "compute")


def test_caller():
    assert cli.run(3) == 7


def test_helper():
    assert engine.helper(3) == 6
