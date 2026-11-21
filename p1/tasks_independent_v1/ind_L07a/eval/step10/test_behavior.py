import rules
import shelf
import views


def test_min_age_revised():
    assert rules.MIN_AGE == 21
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    shelf.insert({"name": "cyd", "age": 30, "score": 40})
    assert [r["name"] for r in shelf.adults()] == ["cyd"]


def test_full_chain():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 25, "score": 80})
    shelf.insert({"name": "bob", "age": 15, "score": 95})
    shelf.insert({"name": "cyd", "age": 40, "score": 60})
    assert shelf.find("bob")["score"] == 95
    assert [r["name"] for r in shelf.filter_by(80)] == ["ann", "bob"]
    assert views.top_names(2) == ["bob", "ann"]
    assert [r["name"] for r in shelf.page(0, 2)] == ["ann", "bob"]
    assert views.summary() == "3 total, 2 adult"
