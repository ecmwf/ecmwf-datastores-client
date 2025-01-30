from __future__ import annotations

from typing import Literal

import pytest
from requests import HTTPError

from datapi import ApiClient, config


@pytest.fixture
def api_client() -> ApiClient:
    try:
        # Can not use anonymous user
        config.get_config("key")
    except Exception:
        pytest.skip("The API key is missing")
    return ApiClient(maximum_tries=0)


@pytest.mark.parametrize("scope", [None, "all", "dataset", "portal"])
def test_profile_accept_licence(
    api_client: ApiClient,
    scope: Literal["all", "dataset", "portal"] | None,
) -> None:
    licence = api_client.get_licences(scope=scope)[0]
    licence_id = licence["id"]
    licence_revision = licence["revision"]

    expected = {"id": licence_id, "revision": licence_revision}
    actual = api_client.accept_licence(licence_id, licence_revision)
    assert expected == actual

    assert any(
        licence["id"] == licence_id and licence["revision"] == licence_revision
        for licence in api_client.get_accepted_licences(scope=scope)
    )


def test_profile_check_authentication(
    api_root_url: str, api_anon_client: ApiClient
) -> None:
    assert api_anon_client.check_authentication() == {
        "email": None,
        "id": -1,
        "role": "anonymous",
        "sub": "anonymous",
    }

    bad_client = ApiClient(key="foo", url=api_root_url)
    with pytest.raises(HTTPError, match="401 Client Error"):
        bad_client.check_authentication()


def test_profile_star_collection(api_client: ApiClient) -> None:
    starred = api_client.star_collection("test-adaptor-dummy")
    assert "test-adaptor-dummy" in starred

    api_client.unstar_collection("test-adaptor-dummy")
    with pytest.raises(HTTPError, match="404 Client Error"):
        api_client.unstar_collection("test-adaptor-dummy")
