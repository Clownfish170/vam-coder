import pytest
import wire


def test_fields():
    assert wire.fields("a=1;b=2") == {"a": "1", "b": "2"}


def test_fields_bad():
    with pytest.raises(ValueError):
        wire.fields("oops")


def test_fields_single():
    assert wire.fields("only=one") == {"only": "one"}


def test_unpack_regression():
    with pytest.raises(ValueError):
        wire.unpack("cmd:")
