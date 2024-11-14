from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from datapi import ApiClient


@pytest.fixture
def api_root_url() -> str:
    from datapi import config

    try:
        return str(config.get_config("url"))
    except Exception:
        return "http://localhost:8080/api"


@pytest.fixture
def api_anon_key() -> str:
    return os.getenv("DATAPI_ANON_KEY", "00112233-4455-6677-c899-aabbccddeeff")


@pytest.fixture
def api_anon_client(api_root_url: str, api_anon_key: str) -> ApiClient:
    from datapi import ApiClient

    return ApiClient(url=api_root_url, key=api_anon_key, maximum_tries=0)
