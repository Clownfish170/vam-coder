import config


def test_timeout():
    assert config.load()["timeout_s"] == 60


def test_retries_unchanged():
    assert config.load()["retries"] == 3


def test_describe():
    import app
    assert "retries=3" in app.describe()
