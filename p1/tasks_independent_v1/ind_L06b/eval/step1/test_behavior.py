import pytest
import wire


def test_empty_payload_rejected():
    with pytest.raises(ValueError):
        wire.unpack("cmd:")


def test_ok_unpack():
    assert wire.unpack("cmd: a=1 ") == ("cmd", " a=1 ")


def test_no_colon():
    with pytest.raises(ValueError):
        wire.unpack("nocolon")


def test_pack_regression():
    assert wire.pack("cmd", "a=1") == "cmd:a=1"
