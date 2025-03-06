import json
import logging

import pytest
import requests
import responses
from responses.matchers import json_params_matcher

from datapi import catalogue, processing

COLLECTION_ID = "reanalysis-era5-pressure-levels"
JOB_SUCCESSFUL_ID = "9bfc1362-2832-48e1-a235-359267420bb2"
JOB_FAILED_ID = "9bfc1362-2832-48e1-a235-359267420bb3"

CATALOGUE_URL = "http://localhost:8080/api/catalogue"
COLLECTIONS_URL = "http://localhost:8080/api/catalogue/v1/datasets"
COLLECTION_URL = (
    "http://localhost:8080/api/catalogue/v1/collections/reanalysis-era5-pressure-levels"
)
PROCESS_URL = f"http://localhost:8080/api/retrieve/v1/processes/{COLLECTION_ID}"
EXECUTE_URL = f"{PROCESS_URL}/execution"

JOB_SUCCESSFUL_URL = f"http://localhost:8080/api/retrieve/v1/jobs/{JOB_SUCCESSFUL_ID}"
JOB_FAILED_URL = f"http://localhost:8080/api/retrieve/v1/jobs/{JOB_FAILED_ID}"

RESULT_SUCCESSFUL_URL = (
    f"http://localhost:8080/api/retrieve/v1/jobs/{JOB_SUCCESSFUL_ID}/results"
)
RESULT_FAILED_URL = (
    f"http://localhost:8080/api/retrieve/v1/jobs/{JOB_FAILED_ID}/results"
)


CATALOGUE_JSON = {
    "type": "Catalog",
    "id": "stac-fastapi",
    "links": [
        {"rel": "self", "type": "application/json", "href": f"{CATALOGUE_URL}/v1"},
        {"rel": "root", "type": "application/json", "href": f"{CATALOGUE_URL}/v1"},
        {"rel": "data", "type": "application/json", "href": f"{COLLECTIONS_URL}"},
        {
            "rel": "child",
            "type": "application/json",
            "title": "ERA5 hourly data on pressure levels from 1959 to present",
            "href": f"{COLLECTION_URL}",
        },
    ],
}

COLLECTIONS_JSON = {
    "collections": [
        {
            "type": "Collection",
            "id": f"{COLLECTION_ID}",
            "links": [
                {
                    "rel": "self",
                    "type": "application/json",
                    "href": f"{COLLECTION_URL}",
                },
                {
                    "rel": "parent",
                    "type": "application/json",
                    "href": f"{CATALOGUE_URL}/v1",
                },
                {
                    "rel": "root",
                    "type": "application/json",
                    "href": f"{CATALOGUE_URL}/v1",
                },
            ],
        },
    ],
    "links": [
        {"rel": "root", "type": "application/json", "href": f"{CATALOGUE_URL}/v1"},
        {"rel": "parent", "type": "application/json", "href": f"{CATALOGUE_URL}/v1"},
        {"rel": "self", "type": "application/json", "href": f"{COLLECTIONS_URL}"},
    ],
}

COLLECTION_JSON = {
    "type": "Collection",
    "id": COLLECTION_ID,
    "links": [
        {
            "rel": "self",
            "type": "application/json",
            "href": "http://localhost:8080/api/catalogue/v1/collections/reanalysis-era5-pressure-levels",
        },
        {
            "rel": "parent",
            "type": "application/json",
            "href": "http://localhost:8080/api/catalogue/v1/",
        },
        {
            "rel": "root",
            "type": "application/json",
            "href": "http://localhost:8080/api/catalogue/v1/",
        },
        {
            "rel": "retrieve",
            "href": "http://localhost:8080/api/retrieve/v1/processes/reanalysis-era5-pressure-levels",
            "type": "application/json",
        },
        {
            "rel": "related",
            "href": "http://localhost:8080/api/catalogue/v1/collections/reanalysis-era5-single-levels",
        },
    ],
    "tmp:variables": {
        "Temperature": {
            "units": "K",
        }
    },
}

PROCESS_JSON = {
    "id": COLLECTION_ID,
    "links": [
        {"href": COLLECTION_URL, "rel": "self", "type": "application/json"},
        {"rel": "retrieve", "href": PROCESS_URL, "type": "application/json"},
        {
            "href": f"{COLLECTION_URL}/execution",
            "rel": "execute",
            "type": "application/json",
            "title": "process execution",
        },
    ],
    "inputs": {
        "product_type": {
            "title": "Product type",
            "schema": {
                "type": "array",
                "items": {"enum": ["ensemble_mean", "reanalysis"], "type": "string"},
            },
        },
        "variable": {
            "title": "Variable",
            "schema": {
                "type": "array",
                "items": {"enum": ["temperature", "vorticity"], "type": "string"},
            },
        },
        "year": {
            "title": "Year",
            "schema": {
                "type": "array",
                "items": {"enum": ["2022", "0000"], "type": "string"},
            },
        },
    },
    "outputs": {
        "download_url": {
            "schema": {"type": "string", "format": "url"},
        }
    },
    "message": "WARNING: This is a warning message",
    "metadata": {
        "datasetMetadata": {
            "messages": [
                {
                    "date": "2023-12-12T13:00:00",
                    "severity": "warning",
                    "content": "This is a warning dataset message",
                },
                {
                    "date": "2023-12-12T14:00:00",
                    "severity": "success",
                    "content": "This is a success dataset message",
                },
            ]
        }
    },
}


JOB_SUCCESSFUL_JSON = {
    "processID": f"{COLLECTION_ID}",
    "type": "process",
    "jobID": f"{JOB_SUCCESSFUL_ID}",
    "status": "successful",
    "created": "2022-09-02T17:30:48.201213",
    "started": "2022-09-02T17:32:43.890617",
    "finished": "2022-09-02T17:32:54.308120",
    "updated": "2022-09-02T17:32:54.308116",
    "links": [
        {"href": f"{JOB_SUCCESSFUL_ID}", "rel": "self", "type": "application/json"},
        {
            "href": f"http://localhost:8080/api/retrieve/v1/jobs/{JOB_SUCCESSFUL_ID}/results",
            "rel": "results",
        },
        {
            "href": f"{JOB_SUCCESSFUL_URL}",
            "rel": "monitor",
            "type": "application/json",
            "title": "job status info",
        },
    ],
    "metadata": {
        "log": [
            ["2024-02-09T09:14:47.811223", "This is a log"],
            ["2024-02-09T09:14:50.811223", "WARNING: This is a warning log"],
        ]
    },
}

JOB_FAILED_JSON = {
    "processID": f"{COLLECTION_ID}",
    "type": "process",
    "jobID": f"{JOB_FAILED_ID}",
    "status": "failed",
    "created": "2022-09-02T17:30:48.201213",
    "started": "2022-09-02T17:32:43.890617",
    "finished": "2022-09-02T17:32:54.308120",
    "updated": "2022-09-02T17:32:54.308116",
    "links": [
        {"href": f"{JOB_FAILED_ID}", "rel": "self", "type": "application/json"},
        {
            "href": f"http://localhost:8080/api/retrieve/v1/jobs/{JOB_FAILED_ID}/results",
            "rel": "results",
        },
        {
            "href": f"{JOB_FAILED_URL}",
            "rel": "monitor",
            "type": "application/json",
            "title": "job status info",
        },
    ],
    "metadata": {
        "log": [
            ["2024-02-09T09:14:47.811223", "This is a log"],
            ["2024-02-09T09:14:50.811223", "WARNING: This is a warning log"],
        ]
    },
}

RESULT_SUCCESSFUL_JSON = {
    "asset": {
        "value": {
            "type": "application/netcdf",
            "href": "./e7d452a747061ab880887d88814bfb0c27593a73cb7736d2dc340852",
            "file:checksum": "e7d452a747061ab880887d88814bfb0c27593a73cb7736d2dc340852",
            "file:size": 8,
            "file:local_path": [
                "/cache-store/",
                "e7d452a747061ab880887d88814bfb0c27593a73cb7736d2dc340852.nc",
            ],
            "xarray:open_kwargs": {},
            "xarray:storage_options": {},
        }
    }
}


RESULT_FAILED_JSON = {
    "type": "job results failed",
    "title": "job failed",
    "status": 400,
    "instance": "http://127.0.0.1:8080/api/retrieve/v1/jobs/02135eee-39a8-4d1f-8cd7-87682de5b981/results",
    "trace_id": "ca3e7170-1ce2-48fc-97f8-bbe64fafce44",
    "traceback": "This is a traceback",
}


@pytest.fixture
def cat() -> catalogue.Catalogue:
    return catalogue.Catalogue(
        CATALOGUE_URL,
        headers={},
        session=requests.Session(),
        retry_options={},
        request_options={},
        download_options={},
        sleep_max=120,
        cleanup=False,
        log_callback=None,
    )


def responses_add() -> None:
    responses.add(
        responses.GET,
        url=f"{CATALOGUE_URL}/v1/",
        json=CATALOGUE_JSON,
        content_type="application/json",
    )

    responses.add(
        responses.GET,
        url=f"{COLLECTIONS_URL}",
        json=COLLECTIONS_JSON,
        content_type="application/json",
    )

    responses.add(
        responses.GET,
        url=f"{COLLECTION_URL}",
        json=COLLECTION_JSON,
        content_type="application/json",
    )

    responses.add(
        responses.GET,
        url=PROCESS_URL,
        json=PROCESS_JSON,
        content_type="application/json",
    )

    responses.add(
        responses.POST,
        url=EXECUTE_URL,
        json=JOB_SUCCESSFUL_JSON,
        match=[
            json_params_matcher(
                {
                    "inputs": {"variable": "temperature", "year": "2022"},
                }
            )
        ],
        content_type="application/json",
    )

    responses.add(
        responses.GET,
        url=JOB_SUCCESSFUL_URL,
        json=JOB_SUCCESSFUL_JSON,
        content_type="application/json",
    )

    responses.add(
        responses.POST,
        url=EXECUTE_URL,
        json=JOB_FAILED_JSON,
        match=[
            json_params_matcher(
                {
                    "inputs": {"variable": "temperature", "year": "0000"},
                }
            )
        ],
        content_type="application/json",
    )

    responses.add(
        responses.GET,
        url=JOB_FAILED_URL,
        json=JOB_FAILED_JSON,
        content_type="application/json",
    )

    responses.add(
        responses.GET,
        url=RESULT_FAILED_URL,
        json=RESULT_FAILED_JSON,
        content_type="application/json",
    )


@responses.activate
def test_catalogue_collections(cat: catalogue.Catalogue) -> None:
    responses_add()
    assert cat.get_collections().json == COLLECTIONS_JSON

    collection = cat.get_collection(COLLECTION_ID)
    assert collection.response.json() == COLLECTION_JSON


@responses.activate
def test_submit(cat: catalogue.Catalogue) -> None:
    responses_add()

    collection = cat.get_collection(COLLECTION_ID)
    assert collection._process.response.json() == PROCESS_JSON

    request = {"variable": "temperature", "year": "2022"}
    remote = collection.submit(request)
    assert remote.json == JOB_SUCCESSFUL_JSON

    remote = collection.submit(request)
    assert remote.url == JOB_SUCCESSFUL_URL
    assert remote.status == "successful"
    assert remote.results_ready is True

    assert remote.created_at.isoformat() == "2022-09-02T17:30:48.201213"
    assert remote.updated_at.isoformat() == "2022-09-02T17:32:54.308116"
    assert remote.started_at is not None
    assert remote.started_at.isoformat() == "2022-09-02T17:32:43.890617"
    assert remote.finished_at is not None
    assert remote.finished_at.isoformat() == "2022-09-02T17:32:54.308120"


@responses.activate
def test_depracations(cat: catalogue.Catalogue) -> None:
    responses_add()

    collection = cat.get_collection(COLLECTION_ID)
    with pytest.warns(DeprecationWarning, match="`process` has been deprecated"):
        assert isinstance(collection.process, processing.Process)

    request = {"variable": "temperature", "year": "2022"}
    remote = collection.submit(request)

    with pytest.warns(
        DeprecationWarning, match="`creation_datetime` has been deprecated"
    ):
        assert remote.creation_datetime.isoformat() == "2022-09-02T17:30:48.201213"

    with pytest.warns(DeprecationWarning, match="`start_datetime` has been deprecated"):
        assert remote.start_datetime is not None
        assert remote.start_datetime.isoformat() == "2022-09-02T17:32:43.890617"

    with pytest.warns(DeprecationWarning, match="`end_datetime` has been deprecated"):
        assert remote.end_datetime is not None
        assert remote.end_datetime.isoformat() == "2022-09-02T17:32:54.308120"


@responses.activate
@pytest.mark.parametrize("method", ("submit", "apply_constraints", "estimate_costs"))
def test_process_docstrings(cat: catalogue.Catalogue, method: str) -> None:
    responses_add()

    collection = cat.get_collection(COLLECTION_ID)
    assert (
        getattr(collection, method).__doc__
        == getattr(collection._process, method).__doc__
    )


@responses.activate
def test_wait_on_result(cat: catalogue.Catalogue) -> None:
    responses_add()

    collection = cat.get_collection(COLLECTION_ID)
    request = {"variable": "temperature", "year": "2022"}
    remote = collection.submit(request)
    remote._wait_on_results()


@responses.activate
def test_wait_on_result_failed(cat: catalogue.Catalogue) -> None:
    responses_add()

    collection = cat.get_collection(COLLECTION_ID)
    request = {"variable": "temperature", "year": "0000"}
    remote = collection.submit(request)
    with pytest.raises(
        processing.ProcessingFailedError,
        match="job failed\nThis is a traceback",
    ):
        remote._wait_on_results()

    assert remote.created_at.isoformat() == "2022-09-02T17:30:48.201213"
    assert remote.started_at is not None
    assert remote.started_at.isoformat() == "2022-09-02T17:32:43.890617"
    assert remote.finished_at is not None
    assert remote.finished_at.isoformat() == "2022-09-02T17:32:54.308120"


@responses.activate
def test_remote_logs(
    caplog: pytest.LogCaptureFixture, cat: catalogue.Catalogue
) -> None:
    responses_add()

    collection = cat.get_collection(COLLECTION_ID)
    request = {"variable": "temperature", "year": "2022"}
    with caplog.at_level(logging.DEBUG, logger="datapi.processing"):
        remote = collection.submit(request)
        remote._wait_on_results()

    assert caplog.record_tuples == [
        (
            "datapi.processing",
            10,
            "GET http://localhost:8080/api/retrieve/v1/processes/reanalysis-era5-pressure-levels",
        ),
        (
            "datapi.processing",
            10,
            f"REPLY {json.dumps(PROCESS_JSON)}",
        ),
        (
            "datapi.processing",
            30,
            "This is a warning message",
        ),
        (
            "datapi.processing",
            30,
            "[2023-12-12T13:00:00] This is a warning dataset message",
        ),
        (
            "datapi.processing",
            20,
            "[2023-12-12T14:00:00] This is a success dataset message",
        ),
        (
            "datapi.processing",
            10,
            (
                "POST http://localhost:8080/api/retrieve/v1/processes/"
                "reanalysis-era5-pressure-levels/execution "
                "{'variable': 'temperature', 'year': '2022'}"
            ),
        ),
        (
            "datapi.processing",
            10,
            f"REPLY {json.dumps(JOB_SUCCESSFUL_JSON)}",
        ),
        (
            "datapi.processing",
            20,
            "Request ID is 9bfc1362-2832-48e1-a235-359267420bb2",
        ),
        (
            "datapi.processing",
            10,
            "GET http://localhost:8080/api/retrieve/v1/jobs/9bfc1362-2832-48e1-a235-359267420bb2",
        ),
        (
            "datapi.processing",
            10,
            f"REPLY {json.dumps(JOB_SUCCESSFUL_JSON)}",
        ),
        ("datapi.processing", 20, "This is a log"),
        ("datapi.processing", 30, "This is a warning log"),
        ("datapi.processing", 20, "status has been updated to successful"),
    ]
