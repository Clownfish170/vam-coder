import json
import pytest
import loader


def test_bad_age(tmp_path):
    p = tmp_path / "p.json"
    p.write_text(json.dumps([{"name": "X", "age": "30"}]),
                 encoding="utf-8")
    with pytest.raises(ValueError):
        loader.load(str(p))


def test_good_age(tmp_path):
    p = tmp_path / "p.json"
    p.write_text(json.dumps([{"name": "X", "age": 7}]),
                 encoding="utf-8")
    assert loader.load(str(p))[0]["age"] == 7


def test_defaults_regression():
    rows = loader.load()
    assert rows[2]["age"] == 0
