from __future__ import annotations

import contextlib
import os
import pathlib
import random
from typing import Any

import pytest
import pytest_httpbin.serve
import requests
import responses

from ecmwf.datastores import Results

does_not_raise = contextlib.nullcontext

RESULTS_URL = "http://localhost:8080/api/retrieve/v1/jobs/9bfc1362-2832-48e1-a235-359267420bb2/results"


@pytest.fixture
def results_json(httpbin: pytest_httpbin.serve.Server) -> dict[str, Any]:
    return {
        "asset": {
            "value": {
                "type": "application/x-grib",
                "href": f"{httpbin.url}/range/10",
                "file:size": 10,
            }
        }
    }


@pytest.fixture
@responses.activate
def results(results_json: dict[str, Any]) -> Results:
    responses.add(
        responses.GET,
        RESULTS_URL,
        json=results_json,
        status=200,
        content_type="application/json",
    )
    return Results.from_request(
        "get",
        RESULTS_URL,
        headers={},
        session=None,
        retry_options={"maximum_tries": 1, "retry_after": 0},
        request_options={},
        download_options={},
        sleep_max=120,
        cleanup=False,
        log_callback=None,
    )


@pytest.mark.parametrize(
    "target,expected",
    [
        ("dummy.grib", "dummy.grib"),
        (None, "10"),
    ],
)
def test_results_download(
    monkeypatch: pytest.MonkeyPatch,
    results: Results,
    tmp_path: pathlib.Path,
    target: str | None,
    expected: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    actual = results.download(target=target)
    assert actual == expected
    assert os.path.getsize(actual) == 10


def test_results_asset(httpbin: pytest_httpbin.serve.Server, results: Results) -> None:
    assert results.asset == {
        "file:size": 10,
        "href": f"{httpbin.url}/range/10",
        "type": "application/x-grib",
    }


def test_results_content_length(results: Results) -> None:
    assert results.content_length == 10


def test_results_content_type(results: Results) -> None:
    assert results.content_type == "application/x-grib"


def test_results_json(results: Results, results_json: dict[str, Any]) -> None:
    assert results.json == results_json


def test_results_location(
    httpbin: pytest_httpbin.serve.Server, results: Results
) -> None:
    assert results.location == f"{httpbin.url}/range/10"


def test_results_url(results: Results) -> None:
    assert results.url == RESULTS_URL


@pytest.mark.parametrize(
    "maximum_tries,raises",
    [
        (500, does_not_raise()),
        (1, pytest.raises(requests.ConnectionError, match="Random error.")),
    ],
)
def test_results_robust_download(
    results: Results,
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

    monkeypatch.setattr(
        requests.Response, "patched_iter_content", patched_iter_content, raising=False
    )
    monkeypatch.setattr(FullHTTPDownloader, "make_stream", make_stream)
    monkeypatch.setitem(results.retry_options, "maximum_tries", maximum_tries)

    target = tmp_path / "test.txt"
    with raises:
        results.download(str(target))
        assert target.stat().st_size == 10
