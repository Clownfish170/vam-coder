import shelf


def _seed():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    shelf.insert({"name": "bob", "age": 15, "score": 90})


def test_find():
    _seed()
    assert shelf.find("bob")["score"] == 90


def test_find_missing():
    _seed()
    assert shelf.find("zz") is None


def test_insert_regression():
    _seed()
    assert len(shelf.RECORDS) == 2
