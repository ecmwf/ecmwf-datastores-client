from __future__ import annotations

import contextlib
import pathlib

import pytest

from ecmwf.datastores import Client, Results

does_not_raise = contextlib.nullcontext


@pytest.fixture
def results(api_anon_client: Client) -> Results:
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
        client = Client(
            url=api_root_url, key=api_anon_key, progress=progress, maximum_tries=0
        )
        submitted = client.submit("test-adaptor-dummy", {})
    submitted.download(target=str(tmp_path / "test.grib"))
    captured = capsys.readouterr()
    assert captured.err if progress else not captured.err


def test_results_override(api_anon_client: Client, tmp_path: pathlib.Path) -> None:
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
