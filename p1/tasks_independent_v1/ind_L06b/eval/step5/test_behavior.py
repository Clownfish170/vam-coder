import pytest
import wire


def test_pack2():
    assert wire.pack2(3, "ping", "a=1") == "#3 ping:a=1"


def test_unpack2():
    assert wire.unpack2("#3 ping:a=1") == (3, "ping", "a=1")


def test_unpack2_bad():
    with pytest.raises(ValueError):
        wire.unpack2("ping:a=1")
    with pytest.raises(ValueError):
        wire.unpack2("#x ping:a=1")


def test_roundtrip_v1():
    assert wire.unpack(wire.pack("k", "v")) == ("k", "v")
