import player


def test_events_playing():
    assert player.available_events("playing") == [
        "pause", "stop", "finish"]


def test_events_ended():
    assert player.available_events("ended") == []


def test_buffering_regression():
    assert player.on_event("idle", "play") == "buffering"
