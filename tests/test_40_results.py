from __future__ import annotations

import os
import pathlib
from typing import Any

import pytest
import pytest_httpbin.serve
import responses

from ecmwf.datastores import Results

RESULTS_URL = "http://localhost:8080/api/retrieve/v1/jobs/9bfc1362-2832-48e1-a235-359267420bb2/results"


@pytest.fixture
def results_json(httpbin: pytest_httpbin.serve.Server) -> dict[str, Any]:
    return {
        "asset": {
            "value": {
                "type": "application/x-grib",
                "href": f"{httpbin.url}/range/1",
                "file:size": 1,
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
        retry_options={"maximum_tries": 1},
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
        (None, "1"),
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
    assert os.path.getsize(actual) == 1


def test_results_asset(httpbin: pytest_httpbin.serve.Server, results: Results) -> None:
    assert results.asset == {
        "file:size": 1,
        "href": f"{httpbin.url}/range/1",
        "type": "application/x-grib",
    }


def test_results_content_length(results: Results) -> None:
    assert results.content_length == 1


def test_results_content_type(results: Results) -> None:
    assert results.content_type == "application/x-grib"


def test_results_json(results: Results, results_json: dict[str, Any]) -> None:
    assert results.json == results_json


def test_results_location(
    httpbin: pytest_httpbin.serve.Server, results: Results
) -> None:
    assert results.location == f"{httpbin.url}/range/1"


def test_results_url(results: Results) -> None:
    assert results.url == RESULTS_URL
