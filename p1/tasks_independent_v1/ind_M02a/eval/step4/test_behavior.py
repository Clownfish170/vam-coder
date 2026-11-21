import loader


def test_v2_default_key():
    assert "full_name" in loader.defaults()
    assert "name" not in loader.defaults()


def test_load_returns_v2():
    rows = loader.load()
    assert rows[0]["full_name"] == "Ann"
    assert "name" not in rows[0]
