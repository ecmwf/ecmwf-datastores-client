# Copyright 2026, European Union.
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

from __future__ import annotations

import pathlib
from collections.abc import Iterator

import pytest
import responses

from ecmwf.datastores import Client

API_URL = "http://localhost:8080/api"
MESSAGES_URL = f"{API_URL}/catalogue/v1/messages"


@pytest.fixture(autouse=True)
def no_config(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    monkeypatch.delenv("ECMWF_DATASTORES_KEY", raising=False)
    monkeypatch.setenv("ECMWF_DATASTORES_RC_FILE", str(tmp_path / "missing"))


@pytest.fixture(autouse=True)
def mock_messages() -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock() as rsps:
        rsps.get(MESSAGES_URL, json={})
        yield rsps


def test_client_missing_key_falls_back_to_anonymous() -> None:
    with pytest.warns(UserWarning, match="falling back to anonymous access") as record:
        client = Client(url=API_URL, maximum_tries=0)
    assert len(record) == 1
    assert client.key is None
    assert set(client._get_headers()) == {"User-Agent"}


@pytest.mark.filterwarnings("error")
def test_client_empty_key_is_anonymous_without_warning() -> None:
    client = Client(url=API_URL, key="", maximum_tries=0)
    assert client.key == ""
    assert set(client._get_headers()) == {"User-Agent"}


@pytest.mark.filterwarnings("error")
def test_client_key_sets_private_token() -> None:
    client = Client(url=API_URL, key="foo", maximum_tries=0)
    headers = client._get_headers()
    assert set(headers) == {"User-Agent", "PRIVATE-TOKEN"}
    assert headers["PRIVATE-TOKEN"] == "foo"


@pytest.mark.filterwarnings("error")
def test_client_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ECMWF_DATASTORES_KEY", "bar")
    client = Client(url=API_URL, maximum_tries=0)
    assert client._get_headers()["PRIVATE-TOKEN"] == "bar"
