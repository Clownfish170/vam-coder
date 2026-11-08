import pipeline
from sinks import emit


def test_emit_through_pipeline():
    assert emit(["a", "b"]) == "v2:a;v2:b"


def test_run_regression():
    assert pipeline.run("z") == "v2:z"
