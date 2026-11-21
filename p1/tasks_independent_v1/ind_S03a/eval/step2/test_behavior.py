import engine
import cli


def test_double_run():
    assert cli.double_run(2) == cli.run(2) + cli.run(3)
    assert cli.double_run(2) == 12


def test_rename_regression():
    assert not hasattr(engine, "compute")
    assert engine.evaluate(3) == 7


def test_run_regression():
    assert cli.run(3) == 7
