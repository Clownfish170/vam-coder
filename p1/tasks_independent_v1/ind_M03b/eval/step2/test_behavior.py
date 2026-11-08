import player


def test_stop_playing():
    assert player.on_event("playing", "stop") == "idle"


def test_stop_paused():
    assert player.on_event("paused", "stop") == "idle"


def test_pause_regression():
    assert player.on_event("playing", "pause") == "paused"
