def test_can_import():
    """
    Checks whether it's possible to import structlog.

    This is used as part of our check whether structlog is importable when
    running with -OO / PYTHONOPTIMIZE=2.
    """
    import structlog

    assert isinstance(structlog.__description__, str)
