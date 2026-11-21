import json
import catalog


def test_default_price(tmp_path):
    p = tmp_path / "i.json"
    p.write_text(json.dumps({"k": {"title": "T"}}),
                 encoding="utf-8")
    assert catalog.load(str(p))["k"]["price"] == 0


def test_existing_price():
    assert catalog.load()["a1"]["price"] == 2
