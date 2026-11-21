import config


def test_workers_in_file():
    assert config.load()["workers"] == 4


def test_banner_format():
    import app
    assert app.banner() == "127.0.0.1:9000 x 4"


def test_port_regression():
    assert config.load()["port"] == 9000
