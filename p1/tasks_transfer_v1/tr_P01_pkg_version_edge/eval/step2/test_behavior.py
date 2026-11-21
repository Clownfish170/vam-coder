from packaging.version import Version

def test_order():
    assert Version("1.2.3") < Version("1.2.4")

def test_str_roundtrip():
    assert str(Version("1.0.0")) == "1.0.0"
