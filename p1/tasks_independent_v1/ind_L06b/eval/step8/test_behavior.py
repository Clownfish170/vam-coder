import pytest
import wire
import bridge


def test_max_seq_constant():
    assert wire.MAX_SEQ == 999


def test_seq_over_limit():
    with pytest.raises(ValueError):
        wire.unpack2("#1000 k:v")


def test_seq_ok():
    assert wire.unpack2("#5 k:v") == (5, "k", "v")


def test_dispatch_regression():
    assert bridge.dispatch("#2 ping:a=1") == "ping"
