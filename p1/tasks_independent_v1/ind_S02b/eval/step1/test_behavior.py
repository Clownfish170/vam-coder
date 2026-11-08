import config


def test_port():
    assert config.load()["port"] == 9000


def test_host_unchanged():
    assert config.load()["host"] == "127.0.0.1"


def test_banner():
    import app
    assert app.banner() == "127.0.0.1:9000"
