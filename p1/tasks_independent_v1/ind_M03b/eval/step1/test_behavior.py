import player


def test_pause():
    assert player.on_event("playing", "pause") == "paused"


def test_resume():
    assert player.on_event("paused", "play") == "playing"


def test_start_regression():
    assert player.on_event("idle", "play") == "playing"
