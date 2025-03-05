from __future__ import annotations

import contextlib
import logging
import os
import pathlib
import time
from typing import Any

import pytest
import requests

from datapi import processing
from datapi.legacy_api_client import LegacyApiClient

does_not_raise = contextlib.nullcontext


@pytest.fixture
def legacy_client(api_root_url: str, api_anon_key: str) -> LegacyApiClient:
    return LegacyApiClient(url=api_root_url, key=api_anon_key, retry_max=1)


def legacy_update(remote: processing.Remote) -> None:
    # See https://github.com/ecmwf/cdsapi/blob/master/examples/example-era5-update.py
    sleep = 1
    while True:
        with pytest.deprecated_call():
            remote.update()

        reply = remote.reply
        remote.info("Request ID: %s, state: %s" % (reply["request_id"], reply["state"]))

        if reply["state"] == "completed":
            break
        elif reply["state"] in ("queued", "running"):
            remote.info("Request ID: %s, sleep: %s", reply["request_id"], sleep)
            time.sleep(sleep)
        elif reply["state"] in ("failed",):
            remote.error("Message: %s", reply["error"].get("message"))
            remote.error("Reason:  %s", reply["error"].get("reason"))
            for n in (
                reply.get("error", {})
                .get("context", {})
                .get("traceback", "")
                .split("\n")
            ):
                if n.strip() == "":
                    break
                remote.error("  %s", n)
            raise Exception(
                "%s. %s."
                % (reply["error"].get("message"), reply["error"].get("reason"))
            )


def test_legacy_api_client_retrieve(
    tmp_path: pathlib.Path, legacy_client: LegacyApiClient
) -> None:
    collection_id = "test-adaptor-dummy"
    request = {"size": 1}
    target = str(tmp_path / "dummy.grib")
    actual_target = legacy_client.retrieve(collection_id, request, target)
    assert target == actual_target
    assert os.path.getsize(target) == 1


def test_legacy_api_client_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
    legacy_client: LegacyApiClient,
) -> None:
    monkeypatch.chdir(tmp_path)

    collection_id = "test-adaptor-dummy"
    request = {"size": 1}
    result = legacy_client.retrieve(collection_id, request)

    target = result.download()
    assert os.path.basename(target) == os.path.basename(result.location)
    assert os.path.getsize(target) == 1

    target = str(tmp_path / "dummy.grib")
    actual_target = result.download(target)
    assert target == actual_target
    assert os.path.getsize(target) == 1

    response = requests.head(result.location)
    assert response.status_code == 200
    assert result.content_length == 1
    assert result.content_type == "application/x-grib"


@pytest.mark.parametrize("quiet", [True, False])
def test_legacy_api_client_quiet(
    caplog: pytest.LogCaptureFixture,
    api_root_url: str,
    api_anon_key: str,
    quiet: bool,
) -> None:
    client = LegacyApiClient(
        url=api_root_url, key=api_anon_key, quiet=quiet, retry_max=0
    )
    client.retrieve("test-adaptor-dummy", {})
    records = [record for record in caplog.records if record.levelname == "INFO"]
    assert not records if quiet else records


@pytest.mark.parametrize("debug", [True, False])
def test_legacy_api_client_debug(
    caplog: pytest.LogCaptureFixture,
    api_root_url: str,
    api_anon_key: str,
    debug: bool,
) -> None:
    LegacyApiClient(url=api_root_url, key=api_anon_key, debug=debug, retry_max=0)
    records = [record for record in caplog.records if record.levelname == "DEBUG"]
    assert records if debug else not records


@pytest.mark.parametrize(
    "wait_until_complete,expected_type",
    [(True, processing.Results), (False, processing.Remote)],
)
def test_legacy_api_client_wait_until_complete(
    tmp_path: pathlib.Path,
    api_root_url: str,
    api_anon_key: str,
    wait_until_complete: bool,
    expected_type: type,
) -> None:
    client = LegacyApiClient(
        url=api_root_url,
        key=api_anon_key,
        wait_until_complete=wait_until_complete,
        retry_max=0,
    )

    collection_id = "test-adaptor-dummy"
    request = {"size": 1}

    result = client.retrieve(collection_id, request)
    assert isinstance(result, expected_type)

    target = tmp_path / "test.grib"
    result.download(str(target))
    assert target.stat().st_size == 1


@pytest.mark.parametrize(
    "collection_id,format,raises",
    [
        ("test-adaptor-dummy", "grib", does_not_raise()),
        (
            "test-adaptor-dummy",
            "foo",
            pytest.raises(Exception, match="400 Client Error"),
        ),
    ],
)
def test_legacy_api_client_update(
    api_root_url: str,
    api_anon_key: str,
    collection_id: str,
    format: str,
    raises: contextlib.nullcontext[Any],
) -> None:
    client = LegacyApiClient(
        url=api_root_url, key=api_anon_key, wait_until_complete=False, retry_max=0
    )
    remote = client.retrieve(collection_id, {"format": format})
    assert isinstance(remote, processing.Remote)
    with raises:
        legacy_update(remote)


@pytest.mark.filterwarnings("ignore:Unverified HTTPS")
def test_legacy_api_client_kwargs(api_root_url: str, api_anon_key: str) -> None:
    session = requests.Session()
    client = LegacyApiClient(
        url=api_root_url,
        key=api_anon_key,
        verify=0,
        timeout=1,
        progress=False,
        delete=True,
        retry_max=2,
        sleep_max=3,
        wait_until_complete=False,
        session=session,
    )
    assert client.client.url == api_root_url
    assert client.client.key == api_anon_key
    assert client.client.verify is False
    assert client.client.timeout == 1
    assert client.client.progress is False
    assert client.client.cleanup is True
    assert client.client.maximum_tries == 2
    assert client.client.sleep_max == 3
    assert client.client.session is session


def test_legacy_api_client_logging(
    caplog: pytest.LogCaptureFixture,
    api_root_url: str,
    api_anon_key: str,
) -> None:
    logger = logging.getLogger("foo")
    client = LegacyApiClient(
        url=api_root_url,
        key=api_anon_key,
        info_callback=logger.info,
        warning_callback=logger.warning,
        error_callback=logger.error,
        debug_callback=logger.debug,
    )
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        client.debug("Debug message")
        client.info("Info message")
        client.warning("Warning message")
        client.error("Error message")
        assert caplog.record_tuples == [
            ("foo", 10, "Debug message"),
            ("foo", 20, "Info message"),
            ("foo", 30, "Warning message"),
            ("foo", 40, "Error message"),
        ]


def test_legacy_api_client_download(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    api_root_url: str,
    api_anon_key: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    client = LegacyApiClient(
        url=api_root_url,
        key=api_anon_key,
        retry_max=1,
        wait_until_complete=False,
    )
    remote = client.retrieve("test-adaptor-dummy", {"size": 1})
    assert isinstance(remote, processing.Remote)
    target = client.download(remote)
    assert os.path.getsize(target) == 1

    results = remote.get_results()
    results_dict = {
        "location": results.location,
        "contentLength": results.content_length,
    }
    results_tuple = (remote, remote.get_results(), results_dict)
    target1 = "remote.grib"
    target2 = "results.grib"
    target3 = "dict.grib"
    targets = [target1, target2, target3]
    assert client.download(results_tuple, targets) == [target1, target2, target3]
    assert all(os.path.getsize(target) == 1 for target in targets)


def test_legacy_api_client_status(legacy_client: LegacyApiClient) -> None:
    status = legacy_client.status()
    assert set(status) <= {
        "critical",
        "fatal",
        "error",
        "warning",
        "warn",
        "info",
        "debug",
        "notset",
    }
    assert all(
        isinstance(value, list) and isinstance(string, str)
        for value in status.values()
        for string in value
    )


def test_legacy_api_client_remote(
    legacy_client: LegacyApiClient, tmp_path: pathlib.Path
) -> None:
    results = legacy_client.retrieve("test-adaptor-dummy", {"size": 1})
    remote = legacy_client.remote(results.location)
    target = str(tmp_path / "dummy.grib")
    actual_target = remote.download(target)
    assert target == actual_target
    assert os.path.getsize(target) == 1


def test_legacy_api_client_warning(
    api_root_url: str,
    api_anon_key: str,
) -> None:
    with pytest.warns(
        UserWarning,
        match="deprecated: {'full_stack': 'a', 'metadata': 'b', 'forget': 'c'}",
    ):
        LegacyApiClient(
            url=api_root_url,
            key=api_anon_key,
            full_stack="a",  # type: ignore[arg-type]
            metadata="b",  # type: ignore[arg-type]
            forget="c",  # type: ignore[arg-type]
        )


def test_legacy_api_client_toolbox(legacy_client: LegacyApiClient) -> None:
    with pytest.raises(NotImplementedError):
        legacy_client.service("service")
    with pytest.raises(NotImplementedError):
        legacy_client.workflow("workflow")
