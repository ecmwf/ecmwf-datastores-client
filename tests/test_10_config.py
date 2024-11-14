import json
import pathlib

import pytest

from datapi import config


def test_read_configuration(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_config = {"url": "dummy-url", "key": "dummy-key"}

    config_file = tmp_path / ".datapi.json"
    with config_file.open("w") as fp:
        json.dump({"url": "dummy-url", "key": "dummy-key"}, fp)

    res = config.read_configuration_file(str(config_file))
    assert res == expected_config

    monkeypatch.setenv("DATAPI_RC", str(config_file))
    res = config.read_configuration_file(None)
    assert res == expected_config


def test_read_configuration_error(tmp_path: pathlib.Path) -> None:
    config_file = tmp_path / ".datapi.json"
    config_file.write_text("XXX")

    with pytest.raises(ValueError):
        config.read_configuration_file(str(config_file))

    with pytest.raises(FileNotFoundError):
        config.read_configuration_file("non-existent-file")


def test_get_config_from_configuration_file(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DATAPI_KEY", raising=False)
    monkeypatch.delenv("DATAPI_URL", raising=False)
    expected_config = {"url": "dummy-url", "key": "dummy-key"}

    config_file = tmp_path / ".datapi.json"
    with config_file.open("w") as fp:
        json.dump(expected_config, fp)

    res = config.get_config("url", str(config_file))
    assert res == expected_config["url"]

    with pytest.raises(KeyError):
        config.get_config("non-existent-key", str(config_file))


def test_get_config_from_environment_variables(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_config = {"url": "dummy-url", "key": "dummy-key"}
    file_config = {"url": "wrong-url", "key": "wrong-key"}

    config_file = tmp_path / ".datapi.json"
    with config_file.open("w") as fp:
        json.dump(file_config, fp)

    monkeypatch.setenv("DATAPI_URL", expected_config["url"])
    monkeypatch.setenv("DATAPI_KEY", expected_config["key"])

    res = config.get_config("url", str(config_file))

    assert res == expected_config["url"]

    res = config.get_config("key", str(config_file))

    assert res == expected_config["key"]
