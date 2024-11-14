import logging

import pytest
from requests import HTTPError

from datapi import ApiClient, Process, Processes, Remote


def test_processig_processes_limit(api_anon_client: ApiClient) -> None:
    processes = api_anon_client.get_processes(limit=1)
    assert isinstance(processes, Processes)
    assert len(processes.collection_ids) == 1
    next_processes = processes.next
    assert next_processes is not None
    assert len(next_processes.collection_ids) == 1


def test_processing_processes_sortby(api_anon_client: ApiClient) -> None:
    processes = api_anon_client.get_processes(sortby="id")
    assert len(processes.collection_ids) > 1
    assert processes.collection_ids == sorted(processes.collection_ids)

    processes = api_anon_client.get_processes(sortby="-id")
    assert processes.collection_ids == sorted(processes.collection_ids, reverse=True)


def test_processing_process(
    caplog: pytest.LogCaptureFixture, api_anon_client: ApiClient
) -> None:
    process = api_anon_client.get_process("test-adaptor-dummy")
    assert isinstance(process, Process)
    assert process.id == "test-adaptor-dummy"

    with caplog.at_level(logging.INFO, logger="datapi.processing"):
        remote = process.submit()
    assert isinstance(remote, Remote)
    assert "The job has been submitted as an anonymous user" in caplog.text


def test_processing_apply_constraints(api_anon_client: ApiClient) -> None:
    result = api_anon_client.apply_constraints(
        "test-adaptor-url", version="deprecated (1.0)"
    )
    assert result["reference_dataset"] == ["cru", "cru_and_gpcc"]

    with pytest.raises(HTTPError, match="invalid param 'foo'"):
        api_anon_client.apply_constraints("test-adaptor-url", foo="bar")


def test_processing_estimate_costs(api_anon_client: ApiClient) -> None:
    result = api_anon_client.estimate_costs("test-adaptor-url", variable=["foo", "bar"])
    assert result == {
        "id": "size",
        "cost": 2.0,
        "limit": 1000.0,
        "cost_bar_steps": None,
    }


def test_processing_get_jobs_status(api_anon_client: ApiClient) -> None:
    remote = api_anon_client.submit("test-adaptor-dummy", format="foo")
    request_uid = remote.request_uid
    with pytest.raises(HTTPError, match="400 Client Error: Bad Request"):
        remote.make_results()
    assert request_uid in api_anon_client.get_jobs(status="failed").request_uids
    assert request_uid not in api_anon_client.get_jobs(status="successful").request_uids


def test_processing_get_jobs_sortby(api_anon_client: ApiClient) -> None:
    uid1 = api_anon_client.submit("test-adaptor-dummy").request_uid
    uid2 = api_anon_client.submit("test-adaptor-dummy").request_uid
    assert [uid2, uid1] == api_anon_client.get_jobs(
        sortby="-created", limit=2
    ).request_uids
    assert [uid2] != api_anon_client.get_jobs(sortby="created", limit=1).request_uids
