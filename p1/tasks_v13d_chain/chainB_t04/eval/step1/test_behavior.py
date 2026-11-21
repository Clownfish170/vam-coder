def test():
    from dispatch import route
    assert route('x') == 'backup'
    assert route('k') == 'main'
