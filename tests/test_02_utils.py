from typing import Any

import pytest

from ecmwf.datastores import utils


@pytest.mark.parametrize(
    "headers,expected",
    [
        (
            {"foo": "bar", "PRIVATE-TOKEN": "foo"},
            "{'foo': 'bar', 'PRIVATE-TOKEN': '***'}",
        ),
        (
            {"foo": "bar", "PRIVATE-TOKEN": None},
            "{'foo': 'bar', 'PRIVATE-TOKEN': None}",
        ),
    ],
)
def test_headers_repr(headers: dict[str, Any], expected: str) -> None:
    assert utils.headers_repr(headers) == expected
