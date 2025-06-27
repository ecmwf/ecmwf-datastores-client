import logging

import pytest
from requests import HTTPError

from ecmwf.datastores import Client, Process, Processes, Remote


def test_processing_processes_limit(api_anon_client: Client) -> None:
    processes = api_anon_client.get_processes(limit=1)
    assert isinstance(processes, Processes)
    assert len(processes.collection_ids) == 1
    next_processes = processes.next
    assert next_processes is not None
    assert len(next_processes.collection_ids) == 1


def test_processing_processes_sortby(api_anon_client: Client) -> None:
    processes = api_anon_client.get_processes(sortby="id")
    assert len(processes.collection_ids) > 1
    assert processes.collection_ids == sorted(processes.collection_ids)

    processes = api_anon_client.get_processes(sortby="-id")
    assert processes.collection_ids == sorted(processes.collection_ids, reverse=True)


def test_processing_process(
    caplog: pytest.LogCaptureFixture, api_anon_client: Client
) -> None:
    process = api_anon_client.get_process("test-adaptor-dummy")
    assert isinstance(process, Process)
    assert process.id == "test-adaptor-dummy"

    with caplog.at_level(logging.INFO, logger="ecmwf.datastores.processing"):
        remote = process.submit({})
    assert isinstance(remote, Remote)
    assert "The job has been submitted as an anonymous user" in caplog.text


def test_processing_apply_constraints(api_anon_client: Client) -> None:
    result = api_anon_client.apply_constraints(
        "test-adaptor-url", {"version": "deprecated (1.0)"}
    )
    assert result["reference_dataset"] == ["cru", "cru_and_gpcc"]

    with pytest.raises(HTTPError, match="invalid param 'foo'"):
        api_anon_client.apply_constraints("test-adaptor-url", {"foo": "bar"})


def test_processing_estimate_costs(api_anon_client: Client) -> None:
    result = api_anon_client.estimate_costs(
        "test-adaptor-url", {"variable": ["foo", "bar"]}
    )
    assert result == {
        "id": "size",
        "cost": 2.0,
        "limit": 1000.0,
    }


def test_processing_get_jobs_status(api_anon_client: Client) -> None:
    remote = api_anon_client.submit("test-adaptor-dummy", {"format": "foo"})
    request_id = remote.request_id
    with pytest.raises(HTTPError, match="400 Client Error: Bad Request"):
        remote.get_results()
    assert request_id in api_anon_client.get_jobs(status="failed").request_ids
    assert request_id not in api_anon_client.get_jobs(status="successful").request_ids


def test_processing_get_jobs_sortby(api_anon_client: Client) -> None:
    id1 = api_anon_client.submit("test-adaptor-dummy", {}).request_id
    id2 = api_anon_client.submit("test-adaptor-dummy", {}).request_id
    ids = api_anon_client.get_jobs(sortby="-created").request_ids
    assert ids.index(id2) < ids.index(id1)
    assert [id2] != api_anon_client.get_jobs(sortby="created", limit=1).request_ids


def test_processing_delete(api_anon_client: Client) -> None:
    id1 = api_anon_client.submit("test-adaptor-dummy", {}).request_id
    id2 = api_anon_client.submit("test-adaptor-dummy", {}).request_id
    job1, job2 = api_anon_client.delete(id1, id2)["jobs"]
    assert job1["status"] == job2["status"] == "dismissed"
    assert job1["jobID"] == id1
    assert job2["jobID"] == id2
