import pytest
import codec


def test_decode_tuple():
    assert codec.decode("hi|there") == ("hi", "there")


def test_decode_missing_sep():
    with pytest.raises(ValueError):
        codec.decode("lonely")


def test_version_prefix_rejected():
    with pytest.raises(ValueError):
        codec.decode("v9|x")


def test_encode_regression():
    assert codec.encode("hi", "there") == "hi|there"
