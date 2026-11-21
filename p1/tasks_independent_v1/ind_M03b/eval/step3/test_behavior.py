import pytest

import player


def test_finish():
    assert player.on_event("playing", "finish") == "ended"


def test_ended_terminal():
    with pytest.raises(ValueError):
        player.on_event("ended", "play")


def test_stop_regression():
    assert player.on_event("playing", "stop") == "idle"
