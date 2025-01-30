import datetime
import filecmp
import os
import pathlib
import zipfile

import pytest
from requests import HTTPError

from datapi import ApiClient


@pytest.mark.extra
def test_adaptors_dummy(api_anon_client: ApiClient, tmp_path: pathlib.Path) -> None:
    collection_id = "test-adaptor-dummy"
    target = str(tmp_path / "dummy.grib")
    remote = api_anon_client.submit(
        collection_id,
        {"_timestamp": datetime.datetime.now().isoformat()},
    )
    assert remote.download(target) == target
    assert os.path.exists(target)


@pytest.mark.extra
def test_adaptors_dummy_cached(
    api_anon_client: ApiClient, tmp_path: pathlib.Path
) -> None:
    collection_id = "test-adaptor-dummy"
    target_grib = str(tmp_path / "dummy.grib")
    request = {
        "size": 1,
        "_timestamp": datetime.datetime.now().isoformat(),
    }
    results = api_anon_client.submit_and_wait_on_results(collection_id, request)
    assert results.content_type == "application/x-grib"
    assert results.download(target_grib) == target_grib
    assert os.path.getsize(target_grib) == 1
    expected_bytes = open(target_grib, "rb").read()

    target_netcdf = str(tmp_path / "dummy.nc")
    results = api_anon_client.submit_and_wait_on_results(
        collection_id, request | {"format": "netcdf"}
    )
    assert results.content_type == "application/netcdf"
    assert results.download(target_netcdf) == target_netcdf
    assert os.path.getsize(target_netcdf) == 1
    assert expected_bytes == open(target_netcdf, "rb").read()

    target_zip = str(tmp_path / "dummy.zip")
    results = api_anon_client.submit_and_wait_on_results(
        collection_id, request | {"format": "zip"}
    )
    assert results.content_type == "application/zip"
    assert results.download(target_zip) == target_zip
    with zipfile.ZipFile(target_zip, "r") as zip_fp:
        with zip_fp.open("dummy_0.grib", "r") as zip_grib_fs:
            assert expected_bytes == zip_grib_fs.read()


@pytest.mark.extra
def test_adaptors_url(api_anon_client: ApiClient, tmp_path: pathlib.Path) -> None:
    collection_id = "test-adaptor-url"
    request = {
        "variable": "grid_point_altitude",
        "reference_dataset": "cru",
        "version": "2_1",
        "format": "zip",
        "_timestamp": datetime.datetime.now().isoformat(),
    }
    target1 = str(tmp_path / "wfde1.zip")
    remote = api_anon_client.submit(collection_id, request)
    assert remote.download(target1) == target1
    assert os.path.exists(target1)

    target2 = str(tmp_path / "wfde2.zip")
    remote = api_anon_client.submit(collection_id, request)
    assert remote.download(target2) == target2
    assert filecmp.cmp(target1, target2)


@pytest.mark.extra
def test_adaptors_url_constraints(
    api_anon_client: ApiClient, tmp_path: pathlib.Path
) -> None:
    with pytest.raises(HTTPError, match="400 Client Error: Bad Request"):
        api_anon_client.submit("test-adaptor-url", {"foo": "bar"})


@pytest.mark.extra
def test_adaptors_direct_mars(
    api_anon_client: ApiClient, tmp_path: pathlib.Path
) -> None:
    collection_id = "test-adaptor-direct-mars"
    request = {
        "levelist": "1",
        "dataset": "reanalysis",
        "time": "00:00:00",
        "param": "155",
        "date": "1940-01-01",
        "expect": "any",
        "levtype": "pl",
        "number": "all",
        "class": "ea",
        "_timestamp": datetime.datetime.now().isoformat(),
    }
    target = str(tmp_path / "era5-complete.grib")
    remote = api_anon_client.submit(collection_id, request)
    assert remote.download(target) == target
    assert os.path.exists(target)


@pytest.mark.extra
def test_adaptors_mars(api_anon_client: ApiClient, tmp_path: pathlib.Path) -> None:
    collection_id = "test-adaptor-mars"
    request = {
        "product_type": "reanalysis",
        "variable": "2m_temperature",
        "year": "2016",
        "month": "01",
        "day": "02",
        "time": "00:00",
        "_timestamp": datetime.datetime.now().isoformat(),
    }
    target = str(tmp_path / "era5.grib")
    remote = api_anon_client.submit(collection_id, request)
    assert remote.download(target) == target
    assert os.path.exists(target)
