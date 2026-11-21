import idna

def test_valid_encode():
    assert idna.encode("example.com") is not None

def test_roundtrip():
    assert idna.decode(idna.encode("example.com")) == "example.com"
