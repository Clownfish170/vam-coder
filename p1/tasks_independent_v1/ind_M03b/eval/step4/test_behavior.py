import player


def test_buffering():
    assert player.on_event("idle", "play") == "buffering"


def test_ready():
    assert player.on_event("buffering", "ready") == "playing"


def test_pause_regression():
    assert player.on_event("playing", "pause") == "paused"


def test_is_playing_regression():
    assert player.is_playing("buffering") is False
