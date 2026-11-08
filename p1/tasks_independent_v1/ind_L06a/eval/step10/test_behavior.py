import codec
import verify


def test_v2_order():
    assert codec.encode2("login", "alice", "urgent") == "v2|login|urgent|alice"
    assert codec.decode2("v2|login|urgent|alice") == ("login", "alice", "urgent")


def test_decode_any_new_order():
    assert codec.decode_any("v2|login|urgent|alice") == ("login", "alice", "urgent")


def test_v1_regression():
    assert codec.encode("k", "v") == "k|v"
    assert codec.decode("k|v") == ("k", "v")


def test_check_regression():
    assert verify.check("v2|login|urgent|alice") is True
    assert codec.negotiate([3, 4]) == 1
