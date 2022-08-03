import json
from mypy_boto3_s3 import S3ServiceResource
from unittest.mock import MagicMock
from urllib.parse import urlparse
from pydantic import ValidationError

import pytest
from pystac import Item
from mypy_boto3_s3.service_resource import Bucket

from src import handler


def test_routing_regex_event(
    monkeypatch: pytest.MonkeyPatch,
    s3_created_bucket: Bucket,
    s3_resource: S3ServiceResource,
):
    """
    Ensure that the system properly routes regex events
    """
    mock_stac_dict = {"mock": "STAC Item"}
    mock_stac_item = MagicMock(spec=Item)
    mock_stac_item.to_dict.return_value = mock_stac_dict
    mock_as_stac = MagicMock(return_value=mock_stac_item)
    monkeypatch.setattr(handler.RegexEvent, "as_stac", mock_as_stac)

    not_called_mock = MagicMock()
    monkeypatch.setattr(handler.CmrEvent, "as_stac", not_called_mock)

    output = handler.handler(
        {
            "collection": "test-collection",
            "s3_filename": "s3://test-bucket/delivery/BMHD_Maria_Stages/70001_BeforeMaria_Stage0_2017-07-21.tif",
            "filename_regex": "^.*.tif$",
            "granule_id": None,
            "datetime_range": None,
            "start_datetime": None,
            "end_datetime": None,
        },
        None,
    )

    mock_stac_item.to_dict.assert_called_once_with()
    assert "stac_file_url" in output
    obj = s3_resource.Object(
        bucket_name=s3_created_bucket.name,
        key=urlparse(output["stac_file_url"]).path.lstrip("/"),
    )
    created_stac_item = json.load(obj.get()["Body"])
    assert created_stac_item == mock_stac_dict
    assert not not_called_mock.call_count


def test_routing_cmr_event(
    monkeypatch: pytest.MonkeyPatch,
    s3_created_bucket: Bucket,
    s3_resource: S3ServiceResource,
):
    """
    Ensure that the system properly routes CMR events
    """
    mock_stac_dict = {"mock": "STAC Item"}
    mock_stac_item = MagicMock(spec=Item)
    mock_stac_item.to_dict.return_value = mock_stac_dict
    mock_as_stac = MagicMock(return_value=mock_stac_item)
    monkeypatch.setattr(handler.CmrEvent, "as_stac", mock_as_stac)

    not_called_mock = MagicMock()
    monkeypatch.setattr(handler.RegexEvent, "as_stac", not_called_mock)

    output = handler.handler(
        {
            "collection": "test-collection",
            "s3_filename": "s3://test-bucket/delivery/BMHD_Maria_Stages/70001_BeforeMaria_Stage0_2017-07-21.tif",
            "granule_id": "test-granule",
        },
        None,
    )

    mock_stac_item.to_dict.assert_called_once_with()
    assert "stac_file_url" in output
    obj = s3_resource.Object(
        bucket_name=s3_created_bucket.name,
        key=urlparse(output["stac_file_url"]).path.lstrip("/"),
    )
    created_stac_item = json.load(obj.get()["Body"])
    assert created_stac_item == mock_stac_dict
    assert not not_called_mock.call_count


@pytest.mark.parametrize(
    "bad_event",
    [
        {
            "collection": "test-collection",
            "s3_filename": "s3://test-bucket/delivery/BMHD_Maria_Stages/70001_BeforeMaria_Stage0_2017-07-21.tif",
        }
    ],
)
def test_routing_unexpected_event(bad_event):
    """
    Ensure that a malformatted event raises a validation error
    """
    with pytest.raises(ValidationError):
        handler.handler(bad_event, None)
