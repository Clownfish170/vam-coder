import app


def test_batch():
    assert app.batch([-1, 5]) == [0, 5]
