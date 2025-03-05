from __future__ import annotations

import os
import pathlib

import pytest
from urllib3.exceptions import InsecureRequestWarning

from datapi import ApiClient, Remote, Results, processing


def test_api_client_download_results(
    api_anon_client: ApiClient, tmp_path: pathlib.Path
) -> None:
    remote = api_anon_client.submit("test-adaptor-dummy", {})
    target = str(tmp_path / "test.grib")

    result = api_anon_client.download_results(remote.request_id, target)
    assert result == target
    assert os.path.exists(result)


def test_api_client_get_process(api_anon_client: ApiClient) -> None:
    process = api_anon_client.get_process("test-adaptor-dummy")
    assert isinstance(process, processing.Process)
    assert process.id == "test-adaptor-dummy"
    assert set(process.headers) == {"User-Agent", "PRIVATE-TOKEN"}


def test_api_client_get_remote(api_anon_client: ApiClient) -> None:
    request_id = api_anon_client.submit("test-adaptor-dummy", {}).request_id
    remote = api_anon_client.get_remote(request_id)
    assert remote.request_id == request_id
    assert set(remote.headers) == {"User-Agent", "PRIVATE-TOKEN"}


def test_api_client_get_results(api_anon_client: ApiClient) -> None:
    request_id = api_anon_client.submit("test-adaptor-dummy", {}).request_id
    results = api_anon_client.get_results(request_id)
    assert isinstance(results, Results)


def test_api_client_retrieve(
    api_anon_client: ApiClient,
    tmp_path: pathlib.Path,
) -> None:
    expected_target = str(tmp_path / "dummy.grib")
    actual_target = api_anon_client.retrieve(
        "test-adaptor-dummy",
        {"size": 1},
        target=expected_target,
    )
    assert expected_target == actual_target
    assert os.path.getsize(actual_target) == 1


def test_api_client_submit(api_anon_client: ApiClient) -> None:
    remote = api_anon_client.submit("test-adaptor-dummy", {})
    assert isinstance(remote, Remote)


def test_api_client_submit_and_wait_on_results(api_anon_client: ApiClient) -> None:
    results = api_anon_client.submit_and_wait_on_results("test-adaptor-dummy", {})
    assert isinstance(results, Results)


def test_api_client_verify(api_root_url: str, api_anon_key: str) -> None:
    if not api_root_url.startswith("https"):
        pytest.skip(f"{api_root_url=} does not use https protocol")
    with pytest.warns(InsecureRequestWarning):
        ApiClient(url=api_root_url, key=api_anon_key, verify=False, maximum_tries=0)


def test_api_client_timeout(
    api_root_url: str,
    api_anon_key: str,
    tmp_path: pathlib.Path,
) -> None:
    with pytest.warns(UserWarning, match="timeout"):
        client = ApiClient(url=api_root_url, key=api_anon_key, timeout=0)
    with pytest.raises(ValueError, match="timeout"):
        client.retrieve("test-adaptor-dummy", {}, target=str(tmp_path / "test.grib"))
