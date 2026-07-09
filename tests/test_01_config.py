# Copyright 2022, European Union.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pathlib

import pytest

from ecmwf.datastores import config


def test_read_configuration(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_config = {"url": "dummy-url", "key": "dummy-key"}

    config_file = tmp_path / ".ecmwfdatastoresrc"
    config_file.write_text("url: dummy-url\nkey: dummy-key")

    res = config.read_config(str(config_file))
    assert res == expected_config

    monkeypatch.setenv("ECMWF_DATASTORES_RC_FILE", str(config_file))
    res = config.read_config(None)
    assert res == expected_config


def test_read_default_config() -> None:
    config_path = pathlib.Path.home() / ".ecmwfdatastoresrc"
    if not config_path.exists():
        with pytest.raises(FileNotFoundError):
            config.read_config()
    else:
        assert config.read_config() == config.read_config(str(config_path))


def test_get_config_from_configuration_file(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ECMWF_DATASTORES_KEY", raising=False)
    monkeypatch.delenv("ECMWF_DATASTORES_URL", raising=False)

    config_file = tmp_path / ".ecmwfdatastoresrc"
    config_file.write_text("url: dummy-url\nkey: dummy-key")

    res = config.get_config("url", str(config_file))
    assert res == "dummy-url"

    with pytest.raises(KeyError):
        config.get_config("non-existent-key", str(config_file))


def test_get_config_from_environment_variables(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected_config = {"url": "dummy-url", "key": "dummy-key"}

    config_file = tmp_path / ".ecmwfdatastoresrc"
    config_file.write_text("url: wrong-url\nkey: wrong-key")

    monkeypatch.setenv("ECMWF_DATASTORES_URL", expected_config["url"])
    monkeypatch.setenv("ECMWF_DATASTORES_KEY", expected_config["key"])

    res = config.get_config("url", str(config_file))

    assert res == expected_config["url"]

    res = config.get_config("key", str(config_file))

    assert res == expected_config["key"]
