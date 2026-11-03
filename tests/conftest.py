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

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from ecmwf.datastores import Client


@pytest.fixture
def api_root_url() -> str:
    from ecmwf.datastores import config

    try:
        return str(config.get_config("url"))
    except Exception:
        return "http://localhost:8080/api"


@pytest.fixture
def api_anon_key() -> str:
    return ""


@pytest.fixture
def api_anon_client(api_root_url: str, api_anon_key: str) -> Client:
    from ecmwf.datastores import Client

    return Client(url=api_root_url, key=api_anon_key, maximum_tries=0)


@pytest.fixture
def api_client() -> Client:
    from ecmwf.datastores import Client, config

    try:
        config.get_config("key")
    except Exception:
        pytest.skip("The API key is missing")
    return Client(maximum_tries=0)
