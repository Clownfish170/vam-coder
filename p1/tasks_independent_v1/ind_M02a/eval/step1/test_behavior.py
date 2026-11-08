import loader


def test_defaults_applied():
    rows = loader.load()
    cy = [r for r in rows if r["name"] == "Cy"][0]
    assert cy["age"] == 0


def test_existing_kept():
    ann = loader.load()[0]
    assert ann["age"] == 30
    assert ann["name"] == "Ann"
