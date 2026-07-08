# ecmwf-datastores-client

[![Static Badge](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity/graduated_badge.svg)](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity#graduated)

ECMWF Data Stores Service (DSS) API Python client.

> [!IMPORTANT]
> This software is **Graduated** and subject to ECMWF's guidelines on [Software Maturity](https://github.com/ecmwf/codex/raw/refs/heads/main/Project%20Maturity).

Technical documentation: https://ecmwf.github.io/ecmwf-datastores-client/

## Installation

Install with conda:

```
$ conda install -c conda-forge ecmwf-datastores-client
```

Install with pip:

```
$ pip install ecmwf-datastores-client
```

## Configuration

The `Client` requires the `url` to the API root and a valid API `key`. These can be provided in three ways, in order of precedence:

1. As keyword arguments when instantiating the `Client`.
1. Via the `ECMWF_DATASTORES_URL` and `ECMWF_DATASTORES_KEY` environment variables.
1. From a configuration file, which must be located at `~/.ecmwfdatastoresrc` or at the path specified by the `ECMWF_DATASTORES_RC_FILE` environment variable.

```
$ cat $HOME/.ecmwfdatastoresrc
url: https://cds.climate.copernicus.eu/api
key: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## Quick Start

Configure the logging level to display INFO messages:

```python
>>> import logging
>>> logging.basicConfig(level="INFO")

```

> [!NOTE]
> All Python code examples in this README are automatically tested as part of the unit test suite.

Instantiate the API client and optionally verify authentication:

```python
>>> from ecmwf.datastores import Client
>>> client = Client()
>>> client.check_authentication()  # optional check
{...}

```

Retrieve data:

```python
>>> collection_id = "reanalysis-era5-pressure-levels"
>>> request = {
...     "product_type": ["reanalysis"],
...     "variable": ["temperature"],
...     "year": ["2022"],
...     "month": ["01"],
...     "day": ["01"],
...     "time": ["00:00"],
...     "pressure_level": ["1000"],
...     "data_format": "grib",
...     "download_format": "unarchived",
... }

>>> client.retrieve(collection_id, request, target="target_1.grib")  # blocks
'target_1.grib'

```

Alternative methods to retrieve data:

```python
>>> remote = client.submit(collection_id, request)  # doesn't block
>>> remote
Remote(...)
>>> remote.download("target_2.grib")  # blocks
'target_2.grib'

>>> results = client.submit_and_wait_on_results(collection_id, request)  # blocks
>>> results
Results(...)
>>> results.download("target_3.grib")
'target_3.grib'

>>> client.download_results(remote.request_id, "target_4.grib")  # blocks
'target_4.grib'

```

List all collection IDs sorted by last update:

```python
>>> collections = client.get_collections(sortby="update")

>>> collection_ids = []
>>> while collections is not None:  # Loop over pages
...     collection_ids.extend(collections.collection_ids)
...     collections = collections.next  # Move to the next page
...

>>> collection_ids
[...]
>>> collection_id in collection_ids
True

```

Explore a collection:

```python
>>> collection = client.get_collection(collection_id)

>>> collection.id == collection_id
True
>>> collection.title
'...'
>>> collection.description
'...'

>>> collection.published_at
datetime.datetime(...)
>>> collection.updated_at
datetime.datetime(...)

>>> collection.begin_datetime
datetime.datetime(...)
>>> collection.end_datetime
datetime.datetime(...)
>>> collection.bbox
(...)

>>> collection.submit(request)
Remote(...)

>>> collection.apply_constraints(request)
{...}

```

Interact with results:

```python
>>> results = client.get_results(remote.request_id)

>>> results.content_length > 0
True
>>> results.content_type
'application/x-grib'
>>> results.location
'...'

>>> results.download("target_5.grib")
'target_5.grib'

```

List all successful jobs, sorted by newest first:

```python
>>> jobs = client.get_jobs(sortby="-created", status="successful")

>>> request_ids = []
>>> while jobs is not None:  # Loop over pages
...     request_ids.extend(jobs.request_ids)
...     jobs = jobs.next  # Move to the next page
...

>>> request_ids
[...]
>>> remote.request_id in request_ids
True

```

Interact with a previously submitted job:

```python
>>> remote = client.get_remote(remote.request_id)

>>> remote.collection_id == collection_id
True
>>> remote.request
{...}

>>> remote.status
'successful'
>>> remote.results_ready
True

>>> remote.created_at
datetime.datetime(...)
>>> remote.started_at
datetime.datetime(...)
>>> remote.finished_at
datetime.datetime(...)
>>> remote.updated_at == remote.finished_at
True

>>> remote.download("target_6.grib")
'target_6.grib'

>>> remote.get_receipt()
{...}

>>> remote.get_results()
Results(...)

>>> remote.delete()
{...}

```

Apply constraints and find the number of available days in a given month:

```python
>>> month = {"year": "2000", "month": "02"}
>>> constrained_request = client.apply_constraints(collection_id, month)

>>> len(constrained_request["day"])
29

```

## Developer Workflow

### 1. Initialise the Repository

Create a repository on GitHub under the ecmwf organisation named ecmwf-datastores-client. Then, run:

```bash
git init -b main
git add .
git commit -m "initialise repository"
git remote add origin git@github.com:ecmwf/ecmwf-datastores-client.git
git push -u origin main
```

### 2. Set Up the Environment

Configure your virtual environment and pre-commit hooks:

```bash
make install
```

> [!NOTE]
> This project uses uv for dependency management. Commit the generated uv.lock file to version control.

### 3. Run Quality Assurance

Check formatting, linting, and lockfile consistency:

```bash
make qa
```

### 4. Commit and Push

Save and push any automatically formatted changes:

```bash
git add .
git commit -m "format codebase and sync lockfile"
git push origin main
```

The CI/CD pipeline triggers on pull requests, merges to main, and new releases.

## Using the Makefile

All development tasks are exposed as self-documenting targets in the `Makefile`. To see a complete list of available targets and their descriptions, run:

```bash
make help
```

This displays all available utility commands, including:

- Environment setup: `make install`
- Quality assurance: `make qa`
- Unit tests: `make unit-tests`
- Type checking: `make type-check`

To run the full set of quality checks, tests, and build steps in a single command, use:

```bash
make all
```

## Instructions for internal dependencies

The CI/CD pipeline is able to clone and install internal ECMWF DSS dependencies. If your package depends on other internal dependencies, follow these steps:

1. In the `pyproject.toml`, add the packages as a Git dependency:

```toml
[project]
dependencies = [
  "dss-package-1 @ git+https://github.com/ecmwf/dss-package-1.git",
  "dss-package-2 @ git+https://github.com/ecmwf/dss-package-2.git",
]
```

2. In the `pyproject.toml`, add the packages to the `uv` workspace configuration as follows:

```toml
[tool.uv.sources]
dss-package-1 = {path = "../dss-package-1", editable = true}
dss-package-2 = {path = "../dss-package-2", editable = true}
```

3. In the `pyproject.toml`, add the packages to the list of repositories to be cloned by the `git-clone` action:

```toml
[tool.git-clone]
repo-list = [
  "ecmwf/dss-package-1",
  "ecmwf/dss-package-2",
]
```

The `git-clone` action will automatically clone the internal dependencies under `../` and check out the appropriate branch. For example, if you open a PR against the upstream branch, it will check out the corresponding upstream branches.

> [!NOTE]
> **Local Development:** If you are working locally and want to run unit tests, it is your responsibility to clone the internal repositories under `../` and check out the correct branches.

## Instructions for PyPI

Publishing to PyPI is done using a Trusted Publisher. See the [PyPI documentation](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).
Configure the Trusted Publisher with the following settings:

- **Owner**: `ecmwf`
- **Repository name**: `ecmwf-datastores-client`
- **Workflow name**: `on-release.yml`
- **Environment name**: `pypi`

## Instructions for GitHub Pages

1. Go to **Settings → Pages**, then set **Source** to **GitHub Actions**.
1. Go to **Settings → Environments → GitHub Pages**, then add a deployment tag rule with the name pattern `"v*"`.

## License

```
Copyright 2022, European Union.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
