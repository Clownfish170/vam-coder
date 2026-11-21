import plug
import shell


def test_run_ok():
    plug.HANDLERS.clear()
    plug.register("echo", lambda x: f"got:{x}")
    assert shell.run("echo", "hi") == "got:hi"


def test_run_missing():
    plug.HANDLERS.clear()
    assert shell.run("nope") == "err:nope"


def test_prompt_regression():
    assert shell.prompt() == ">"


def test_names_regression():
    plug.HANDLERS.clear()
    plug.register("x", lambda: 1)
    assert plug.names() == ["x"]
