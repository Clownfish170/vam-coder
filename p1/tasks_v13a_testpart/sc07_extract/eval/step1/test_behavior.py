def test():
    from app import get
    assert get() == 42
