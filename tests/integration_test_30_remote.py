import contextlib
import datetime
import os
import pathlib
import uuid
from typing import Any

import pytest
from requests import HTTPError

from datapi import ApiClient, Remote

does_not_raise = contextlib.nullcontext


@pytest.fixture
def remote(api_anon_client: ApiClient) -> Remote:
    return api_anon_client.submit("test-adaptor-dummy", size=1)


def test_remote_delete(remote: Remote) -> None:
    result = remote.delete()
    assert result["status"] == "dismissed"

    with pytest.raises(HTTPError, match="404 Client Error"):
        remote.status


def test_remote_download(remote: Remote, tmp_path: pathlib.Path) -> None:
    target = str(tmp_path / "dummy.grib")
    result = remote.download(target=target)
    assert result == target
    assert os.path.getsize(result) == 1


def test_remote_collection_id(remote: Remote) -> None:
    assert remote.collection_id == "test-adaptor-dummy"


def test_remote_json(remote: Remote) -> None:
    assert isinstance(remote.json, dict)


def test_remote_request(remote: Remote) -> None:
    assert remote.request == {
        "elapsed": 0.0,
        "format": "grib",
        "size": 1,
    }


def test_remote_request_uid(remote: Remote) -> None:
    assert uuid.UUID(remote.request_uid)


def test_remote_status(remote: Remote) -> None:
    assert remote.status in ("accepted", "running", "successful")


def test_remote_failed(api_anon_client: ApiClient) -> None:
    remote = api_anon_client.submit("test-adaptor-dummy", format="foo")
    with pytest.raises(HTTPError, match="400 Client Error: Bad Request"):
        remote.download()
    assert remote.status == "failed"


@pytest.mark.parametrize(
    "cleanup,raises",
    [
        (True, pytest.raises(HTTPError, match="404 Client Error")),
        (False, does_not_raise()),
    ],
)
def test_remote_cleanup(
    api_root_url: str,
    api_anon_key: str,
    cleanup: bool,
    raises: contextlib.nullcontext[Any],
) -> None:
    client = ApiClient(
        url=api_root_url, key=api_anon_key, cleanup=cleanup, maximum_tries=0
    )
    remote = client.submit("test-adaptor-dummy")
    request_uid = remote.request_uid
    del remote

    client = ApiClient(url=api_root_url, key=api_anon_key, maximum_tries=0)
    with raises:
        client.get_remote(request_uid)


def test_remote_datetimes(api_anon_client: ApiClient) -> None:
    remote = api_anon_client.submit(
        "test-adaptor-dummy",
        elapsed=1,
        _timestamp=datetime.datetime.now().isoformat(),
    )
    assert remote.results_ready is False
    assert isinstance(remote.creation_datetime, datetime.datetime)
    assert remote.end_datetime is None

    remote.make_results()
    assert remote.start_datetime is not None
    assert remote.end_datetime is not None
    assert remote.creation_datetime < remote.start_datetime < remote.end_datetime
