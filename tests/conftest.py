from __future__ import annotations

import os
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
    return os.getenv("ANONYMOUS_PAT", "00112233-4455-6677-c899-aabbccddeeff")


@pytest.fixture
def api_anon_client(api_root_url: str, api_anon_key: str) -> Client:
    from ecmwf.datastores import Client

    return Client(url=api_root_url, key=api_anon_key, maximum_tries=0)
