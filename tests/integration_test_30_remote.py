from __future__ import annotations

import contextlib
import datetime
import os
import pathlib
import time
import uuid
from typing import Any

import pytest
from requests import HTTPError

import ecmwf.datastores.processing
from ecmwf.datastores import Client, Remote

does_not_raise = contextlib.nullcontext


@pytest.fixture
def remote(api_anon_client: Client) -> Remote:
    return api_anon_client.submit("test-adaptor-dummy", {"size": 1})


def test_remote_delete(remote: Remote) -> None:
    result = remote.delete()
    time.sleep(1)
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


def test_remote_request_id(remote: Remote) -> None:
    assert uuid.UUID(remote.request_id)


def test_remote_status(remote: Remote) -> None:
    assert remote.status in ("accepted", "running", "successful")


def test_remote_failed(api_anon_client: Client) -> None:
    remote = api_anon_client.submit("test-adaptor-dummy", {"format": "foo"})
    with pytest.raises(HTTPError, match="400 Client Error: Bad Request"):
        remote.download()
    assert remote.status == "failed"


@pytest.mark.parametrize("cleanup", (True, False))
def test_remote_cleanup(
    api_root_url: str,
    api_anon_key: str,
    cleanup: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MockRemote(Remote):
        delete_count = 0

        def delete(self) -> dict[str, Any]:
            self.delete_count += 1
            return {}

    monkeypatch.setattr(ecmwf.datastores.processing, "Remote", MockRemote)

    client = Client(
        url=api_root_url, key=api_anon_key, cleanup=cleanup, maximum_tries=0
    )
    remote = client.submit("test-adaptor-dummy", {})
    assert isinstance(remote, MockRemote)
    remote.__del__()
    assert remote.delete_count == cleanup


def test_remote_datetimes(api_anon_client: Client) -> None:
    request = {"elapsed": 1, "_timestamp": datetime.datetime.now().isoformat()}
    remote = api_anon_client.submit("test-adaptor-dummy", request)
    assert remote.results_ready is False
    assert isinstance(remote.created_at, datetime.datetime)
    assert remote.finished_at is None

    remote.get_results()
    assert remote.started_at is not None
    assert remote.finished_at is not None
    assert remote.created_at < remote.started_at < remote.finished_at
    assert remote.finished_at == remote.updated_at
