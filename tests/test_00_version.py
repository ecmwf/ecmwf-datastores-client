import ecmwf.datastores


def test_version() -> None:
    assert ecmwf.datastores.__version__ != "999"
