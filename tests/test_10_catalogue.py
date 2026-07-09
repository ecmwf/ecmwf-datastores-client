# Copyright 2022, European Union.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import pytest
import responses

from ecmwf.datastores import Collection

COLLECTION_URL = (
    "http://localhost:8080/api/catalogue/v1/collections/reanalysis-era5-pressure-levels"
)
COLLECTION_JSON = {
    "id": "reanalysis-era5-pressure-levels",
    "extent": {
        "spatial": {"bbox": [[0.0, -89.0, 360.0, 89.0]]},
        "temporal": {"interval": [["1959-01-01T00:00:00Z", "2025-01-10T00:00:00Z"]]},
    },
    "published": "1990-01-01T00:00:00Z",
    "updated": "1991-01-01T00:00:00Z",
    "title": "This is a title",
    "description": "This is a description",
}


@pytest.fixture
@responses.activate
def collection() -> Collection:
    responses.add(
        responses.GET,
        COLLECTION_URL,
        json=COLLECTION_JSON,
        status=200,
        content_type="application/json",
    )
    return Collection.from_request(
        "get",
        COLLECTION_URL,
        headers={},
        session=None,
        retry_options={"maximum_tries": 1},
        request_options={},
        download_options={},
        sleep_max=120,
        cleanup=False,
        log_callback=None,
    )


def test_catalogue_collection_begin_datetime(collection: Collection) -> None:
    assert collection.begin_datetime is not None
    assert collection.begin_datetime.isoformat() == "1959-01-01T00:00:00+00:00"


def test_catalogue_collection_end_datetime(collection: Collection) -> None:
    assert collection.end_datetime is not None
    assert collection.end_datetime.isoformat() == "2025-01-10T00:00:00+00:00"


def test_catalogue_collection_published_at(collection: Collection) -> None:
    assert collection.published_at.isoformat() == "1990-01-01T00:00:00+00:00"


def test_catalogue_collection_updated_at(collection: Collection) -> None:
    assert collection.updated_at.isoformat() == "1991-01-01T00:00:00+00:00"


def test_catalogue_collection_title(collection: Collection) -> None:
    assert collection.title == "This is a title"


def test_catalogue_collection_description(collection: Collection) -> None:
    assert collection.description == "This is a description"


def test_catalogue_collection_bbox(collection: Collection) -> None:
    assert collection.bbox == (0, -89, 360, 89)


def test_catalogue_collection_id(collection: Collection) -> None:
    assert collection.id == "reanalysis-era5-pressure-levels"


def test_catalogue_collection_json(collection: Collection) -> None:
    assert collection.json == COLLECTION_JSON


def test_catalogue_collection_url(collection: Collection) -> None:
    assert collection.url == COLLECTION_URL
