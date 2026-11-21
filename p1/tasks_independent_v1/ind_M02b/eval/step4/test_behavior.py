import catalog


def test_v2_values():
    data = catalog.load()
    assert data["a1"]["cost_cents"] == 200
    assert data["a2"]["cost_cents"] == 500
    assert "price" not in data["a1"]


def test_v2_default(tmp_path):
    import json
    p = tmp_path / "i.json"
    p.write_text(json.dumps({"k": {"title": "T"}}),
                 encoding="utf-8")
    assert catalog.load(str(p))["k"]["cost_cents"] == 0
