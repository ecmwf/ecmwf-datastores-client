# AGENTS.md — ecmwf-datastores-client

Python client for the ECMWF Data Stores Service (DSS) API. Enables browsing, submitting, and downloading climate/weather datasets (ERA5, CDS, etc.).

## Using the Client (for AI agents helping users)

This section describes how to help users retrieve data with this package.

### Setup

Credentials live in `~/.ecmwfdatastoresrc` (see the Config section below). If a user has not set up credentials, guide them to add the file before doing anything else.

```python
import logging

logging.basicConfig(level="INFO")  # shows job status updates while polling

from ecmwf.datastores import Client

client = Client()  # reads URL + key from config or env vars
```

### Request structure

A request is a plain `dict[str, Any]` passed to `client.retrieve()`, `client.submit()`, or `client.apply_constraints()`. Values can be a single item **or a list**; the API accepts both.

```python
request = {
    "product_type": ["reanalysis"],  # list or single string
    "variable": ["temperature"],
    "year": ["2022"],
    "month": ["01"],
    "day": ["01"],
    "time": ["00:00"],
    "pressure_level": ["1000"],
    "data_format": "grib",  # "grib" or "netcdf"
    "download_format": "unarchived",  # "unarchived" or "zip"
}
```

There is no fixed schema enforced client-side. The exact keys and valid values depend on the collection. Use `apply_constraints` (below) to discover them.

### Discovering valid request parameters

**Step 1 — Find a collection ID.** Browse the catalogue to discover what datasets exist:

```python
collections = client.get_collections(sortby="update")
while collections is not None:
    print(collections.collection_ids)
    collections = collections.next  # follow pagination
```

Or search by keyword/text:

```python
collections = client.get_collections(query="ERA5", keywords=["Reanalysis"])
```

**Step 2 — Inspect the collection.** A `Collection` object exposes metadata:

```python
col = client.get_collection("reanalysis-era5-pressure-levels")
print(col.title, col.description)
print(col.begin_datetime, col.end_datetime)  # temporal coverage
print(col.bbox)  # spatial bounding box
```

**Step 3 — Apply constraints to narrow valid values.** `apply_constraints` sends a partial or complete request to the API and returns only the values that are valid given the current selections. Use it iteratively to build up a valid request or to check what is available:

```python
# What days exist for February 2000 (e.g. check for leap year)?
partial = {"year": "2000", "month": "02"}
constrained = client.apply_constraints("reanalysis-era5-pressure-levels", partial)
print(constrained["day"])  # returns list of valid day strings

# Validate a complete request before submitting
constrained = client.apply_constraints("reanalysis-era5-pressure-levels", request)
# If a field in `request` has no valid intersection, it will be absent or empty in the response.
```

`apply_constraints` is also available directly on a `Collection` or `Process` object:

```python
process = client.get_process(collection_id)
constrained = process.apply_constraints(request)
```

### Retrieving data

**Blocking (simplest):** submit, wait, download, return path:

```python
path = client.retrieve(collection_id, request, target="output.grib")
```

**Non-blocking submit, then download later:**

```python
remote = client.submit(collection_id, request)
print(remote.request_id)  # save this to re-attach later

# ...later or in a different process...
remote = client.get_remote(remote.request_id)
path = remote.download("output.grib")
```

**Submit and wait, then inspect before downloading:**

```python
results = client.submit_and_wait_on_results(collection_id, request)
print(results.content_length, results.content_type)  # e.g. 'application/x-grib'
path = results.download("output.grib")
```

If `target` is omitted from any download call the file is saved to the current working directory with a server-assigned name.

### Monitoring jobs

```python
remote = client.get_remote(request_id)
print(remote.status)  # 'accepted' | 'running' | 'successful' | 'failed' | 'rejected'
print(remote.created_at)  # datetime
print(remote.started_at)  # datetime or None
print(remote.finished_at)  # datetime or None
print(remote.results_ready)  # True once status == 'successful'
```

List all jobs (paginated):

```python
jobs = client.get_jobs(sortby="-created", status="successful")
while jobs is not None:
    print(jobs.request_ids)
    jobs = jobs.next
```

### Error handling

| Exception | When raised |
|---|---|
| `ProcessingFailedError` | Job enters `failed`, `rejected`, `dismissed`, or `deleted` state |
| `DownloadError` | Downloaded file size does not match `Content-Length` |
| `requests.HTTPError` | HTTP 4xx/5xx (message includes structured API error detail) |

```python
import requests
from ecmwf.datastores.processing import ProcessingFailedError

try:
    path = client.retrieve(collection_id, bad_request, target="out.grib")
except ProcessingFailedError as e:
    print("Job failed:", e)
except requests.HTTPError as e:
    print("HTTP error:", e)
```

### Licences

Some collections require accepting a licence before data can be retrieved. The API will return a 4xx error with a message indicating which licence is needed.

```python
licences = client.get_licences()  # all available licences
accepted = client.get_accepted_licences()  # already accepted

client.accept_licence(licence_id="licence-to-use-copernicus-products", revision=12)
```

### Estimate costs before submitting

```python
costs = client.estimate_costs(collection_id, request)
print(costs)  # dict with cost metadata
```

### Cleaning up jobs

```python
client.delete(request_id)  # delete one job
client.delete(id1, id2, id3)  # delete multiple jobs

# Auto-delete on completion (sets cleanup=True globally):
client = Client(cleanup=True)
```

## Architecture

```
ecmwf/datastores/
├── client.py        # High-level Client facade — the only class users instantiate
├── catalogue.py     # Collections/Collection: browse datasets
├── processing.py    # Jobs, Remote, Results, Process: submit/poll/download
├── profile.py       # Auth checks, licences, starred collections
├── config.py        # Config resolution (constructor → env var → RC file)
├── legacy_client.py # Backward-compat shim subclassing cdsapi.api.Client
└── utils.py         # string_to_datetime helper only
```

All non-trivial classes use `@attrs.define`. Use `@attrs.define(slots=False)` whenever `functools.cached_property` appears in the same class — `slots=True` (the default) is incompatible with it.

HTTP is handled by `multiurl`. All requests flow through `ApiResponse.from_request()` in `processing.py`. Never call `requests` directly.

## Config

Config for `url` and `key` resolves in this order:

1. Constructor kwargs: `Client(url=..., key=...)`
1. Env vars: `ECMWF_DATASTORES_URL`, `ECMWF_DATASTORES_KEY`
1. RC file: `~/.ecmwfdatastoresrc` (or path in `ECMWF_DATASTORES_RC_FILE`)

RC file format (custom line-based parser, not YAML):

```
url: https://cds.climate.copernicus.eu/api
key: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

A missing key at `Client.__init__` time raises only a `UserWarning`; a `ValueError` is raised only when a key-protected endpoint is called.

## Key Patterns

- **All code is synchronous** — no `asyncio`, no threads. Polling uses `time.sleep`.
- **`from __future__ import annotations`** is used in every module.
- **Retry** is automatic via `multiurl.robust`; do not add manual retry loops.
- **Logging** goes through a `log_callback` function pointer, not direct `logging` calls. Match this pattern when adding new log output in `processing.py`.
- **Polling** uses exponential back-off (1 s × 1.5, capped at `sleep_max=120 s`) inside `Remote._wait_on_results()`.
- **Cleanup** — `Remote.__del__` calls `delete()` when `cleanup=True`. Preserve this pattern.
- **Error types** to raise/handle: `ProcessingFailedError`, `DownloadError`, `LinkError` (all in `processing.py`). For 4xx HTTP errors use `cads_raise_for_status`, which extracts structured error details from the JSON body.

## Public API Surface

Anything exported from `ecmwf/datastores/__init__.py` is public. Keep that list stable. The main entry point for all operations is `Client`.

## Legacy Client

`LegacyClient` (`legacy_client.py`) is a compatibility shim over `cdsapi.api.Client`. It:

- Reads config via `cdsapi` conventions (`~/.cdsapirc`, `CDSAPI_*` env vars)
- Delegates all real work to an internal `datastores.Client` instance
- Must keep `cdsapi` as an **optional** dependency (`pip install ".[legacy]"`)

Do not add new user-facing features to `LegacyClient`. New features belong in `Client`.

## Build and Test

```bash
# Install
pip install -e .
pip install -e ".[legacy]"   # includes cdsapi shim

# Linting and type-checking
make qa                       # pre-commit (ruff + mypy) over all files
make type-check               # mypy --strict

# Unit tests (no live server required)
make unit-tests               # pytest with coverage

# Integration tests (require a live API server)
make integration-tests        # pytest tests/integration_test_*.py

# Doc tests (README.md doctests)
make doc-tests
```

Before submitting changes, run `make qa` and `make unit-tests`. Integration tests need a running DSS server — skip them unless specifically required.

## Type Checking

`mypy` runs with `strict=True`. All new code must pass without `# type: ignore` unless unavoidable (document why). `typing_extensions.Self` is used for Python < 3.11 compatibility; the project supports Python 3.9–3.14.

## Linting

`ruff` enforces: pyflakes (F), pycodestyle (E/W), isort (I), pydocstyle (D, NumPy convention), flake8-future-annotations (FA), pyupgrade (UP). Line length 88 (Black). Do not disable rules without a clear reason.

## Adding a New Client Method

1. Implement the underlying API call in `catalogue.py`, `processing.py`, or `profile.py`.
1. Expose it on `Client` in `client.py` by delegating to the appropriate module object.
1. Export the new type (if any) from `__init__.py`.
1. Add a unit test in `tests/test_*.py` and an integration test in the matching `tests/integration_test_*.py`.

## Integration Test Setup

Integration tests read configuration from:

- `ECMWF_DATASTORES_URL` env var (default: `http://localhost:8080/api`)
- `ANONYMOUS_PAT` env var for an anonymous API key

They assume the server hosts `test-adaptor-dummy`, `test-adaptor-mars`, and `test-adaptor-url` collections. Profile tests that modify state (licence acceptance, starring) are skipped when no real user key is available.

Tests marked `@pytest.mark.extra` are excluded from default CI runs (`make ci-integration-tests` adds `-m "not extra"`).

## version.py

`ecmwf/datastores/version.py` is **generated by `setuptools_scm`** at install time and is gitignored. Do not create or edit it manually. The `__init__.py` handles a missing file gracefully by falling back to `"999"`.
