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

import pytest

from ecmwf.datastores import Client, Collection, processing


@pytest.fixture
def collection(api_anon_client: Client) -> Collection:
    return api_anon_client.get_collection("test-adaptor-mars")


def test_catalogue_collections(api_anon_client: Client) -> None:
    collections = api_anon_client.get_collections()
    assert collections.next is not None

    collection_ids = list(collections.collection_ids)
    while len(collection_ids) != collections.json["numberMatched"]:
        assert "search" not in collections.json
        assert (next_collections := collections.next) is not None
        collections = next_collections
        collection_ids.extend(collections.collection_ids)
    assert "reanalysis-era5-single-levels" in collection_ids


def test_catalogue_collections_limit(api_anon_client: Client) -> None:
    collections = api_anon_client.get_collections(limit=1)
    assert len(collections.collection_ids) == 1


def test_catalogue_collections_sortby(api_anon_client: Client) -> None:
    collections_title = api_anon_client.get_collections(sortby="title")
    collections_relevance = api_anon_client.get_collections(sortby="relevance")
    assert collections_title.collection_ids != collections_relevance.collection_ids


def test_catalogue_collections_query(api_anon_client: Client) -> None:
    collections = api_anon_client.get_collections(query="test")
    assert collections.collection_ids


def test_catalogue_collections_keywords(api_anon_client: Client) -> None:
    collections = api_anon_client.get_collections(keywords=["Product type: Reanalysis"])
    assert collections.collection_ids


def test_catalogue_collection_begin_datetime(collection: Collection) -> None:
    assert collection.begin_datetime is not None
    assert collection.begin_datetime.isoformat() == "1959-01-01T00:00:00+00:00"


def test_catalogue_collection_end_datetime(collection: Collection) -> None:
    assert collection.end_datetime is not None
    assert collection.end_datetime.isoformat() == "2023-05-09T00:00:00+00:00"


def test_catalogue_collection_published_at(collection: Collection) -> None:
    assert collection.published_at.isoformat() == "2018-06-14T00:00:00+00:00"


def test_catalogue_collection_updated_at(collection: Collection) -> None:
    assert collection.updated_at.isoformat() == "2023-05-15T00:00:00+00:00"


def test_catalogue_collection_title(collection: Collection) -> None:
    assert (
        collection.title
        == "TEST DATASET for MarsCdsAdaptor based on: ERA5 hourly data on single levels from 1940 to present"
    )


def test_catalogue_collection_description(collection: Collection) -> None:
    assert collection.description == (
        "ERA5 is the fifth generation ECMWF reanalysis for the global climate and weather for the past 8"
        " decades.\nData is available from 1940 onwards.\nERA5 replaces the ERA-Interim reanalysis."
    )


def test_catalogue_collection_bbox(collection: Collection) -> None:
    assert collection.bbox == (0, -89, 360, 89)


def test_catalogue_collection_id(collection: Collection) -> None:
    assert collection.id == "test-adaptor-mars"


def test_catalogue_collection_json(collection: Collection) -> None:
    assert isinstance(collection.json, dict)


def test_catalogue_collection_process(collection: Collection) -> None:
    process = collection._process
    assert isinstance(process, processing.Process)
    assert process.id == "test-adaptor-mars"


def test_catalogue_collection_url(collection: Collection) -> None:
    assert collection.url.endswith("collections/test-adaptor-mars")


def test_catalogue_get_licences(api_anon_client: Client) -> None:
    all_licences = api_anon_client.get_licences(scope="all")
    assert all("id" in licence and "revision" in licence for licence in all_licences)

    portal_licences = api_anon_client.get_licences(scope="portal")
    assert portal_licences
    for portal_licence in portal_licences:
        assert portal_licence in all_licences


def test_catalogue_form(collection: Collection) -> None:
    assert set(collection.form[0]) == {
        "css",
        "default",
        "details",
        "help",
        "id",
        "label",
        "name",
        "required",
        "type",
    }


def test_catalogue_constraints(collection: Collection) -> None:
    assert set(collection.constraints[0]) == {
        "day",
        "month",
        "product_type",
        "time",
        "variable",
        "year",
    }
