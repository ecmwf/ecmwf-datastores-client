from __future__ import annotations

import contextlib
import pathlib
import random
from typing import Any

import pytest
import requests

from datapi import ApiClient, Results

does_not_raise = contextlib.nullcontext


@pytest.fixture
def results(api_anon_client: ApiClient) -> Results:
    return api_anon_client.submit_and_wait_on_results("test-adaptor-dummy", {"size": 1})


def test_results_asset(results: Results) -> None:
    assert results.asset["type"] == "application/x-grib"
    assert results.asset["file:size"] == 1


@pytest.mark.parametrize("progress", [True, False])
def test_results_progress(
    api_root_url: str,
    api_anon_key: str,
    tmp_path: pathlib.Path,
    progress: bool,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with capsys.disabled():
        client = ApiClient(
            url=api_root_url, key=api_anon_key, progress=progress, maximum_tries=0
        )
        submitted = client.submit("test-adaptor-dummy", {})
    submitted.download(target=str(tmp_path / "test.grib"))
    captured = capsys.readouterr()
    assert captured.err if progress else not captured.err


@pytest.mark.parametrize(
    "maximum_tries,raises",
    [
        (500, does_not_raise()),
        (1, pytest.raises(requests.ConnectionError, match="Random error.")),
    ],
)
def test_results_robust_download(
    api_root_url: str,
    api_anon_key: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    maximum_tries: int,
    raises: contextlib.nullcontext[Any],
) -> None:
    from multiurl.http import FullHTTPDownloader

    def patched_iter_content(self, *args, **kwargs):  # type: ignore
        for chunk in self.iter_content(chunk_size=1):
            if random.choice([True, False]):
                raise requests.ConnectionError("Random error.")
            yield chunk

    def make_stream(self):  # type: ignore
        request = self.issue_request(self.range)
        return request.patched_iter_content

    client = ApiClient(
        url=api_root_url, key=api_anon_key, retry_after=0, maximum_tries=maximum_tries
    )
    results = client.submit_and_wait_on_results("test-adaptor-dummy", {"size": 10})
    monkeypatch.setattr(
        requests.Response, "patched_iter_content", patched_iter_content, raising=False
    )
    monkeypatch.setattr(FullHTTPDownloader, "make_stream", make_stream)

    target = tmp_path / "test.grib"
    with raises:
        results.download(str(target))


def test_results_override(api_anon_client: ApiClient, tmp_path: pathlib.Path) -> None:
    target_1 = tmp_path / "tmp1.grib"
    api_anon_client.retrieve("test-adaptor-dummy", {"size": 1}, target=str(target_1))

    target_2 = tmp_path / "tmp2.grib"
    api_anon_client.retrieve("test-adaptor-dummy", {"size": 2}, target=str(target_2))

    target = tmp_path / "tmp.grib"
    api_anon_client.retrieve("test-adaptor-dummy", {"size": 1}, target=str(target))
    assert target.read_bytes() == target_1.read_bytes()
    api_anon_client.retrieve("test-adaptor-dummy", {"size": 2}, target=str(target))
    assert target.read_bytes() == target_2.read_bytes()
    api_anon_client.retrieve("test-adaptor-dummy", {"size": 1}, target=str(target))
    assert target.read_bytes() == target_1.read_bytes()
