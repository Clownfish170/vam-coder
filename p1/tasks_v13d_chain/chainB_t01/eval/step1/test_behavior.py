def test():
    from dispatch import route
    assert route('') == 'backup'
    assert route('k') == 'main'
    assert route(None) == 'main'
