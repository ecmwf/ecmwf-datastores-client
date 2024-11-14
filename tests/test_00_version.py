import datapi


def test_version() -> None:
    assert datapi.__version__ != "999"
