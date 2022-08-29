import contextlib
from typing import TYPE_CHECKING, Any, Type
from unittest.mock import MagicMock, Mock
from pydantic import ValidationError

import pytest
from pystac import Item

import handler
from utils import stac, events

if TYPE_CHECKING:
    from functools import _SingleDispatchCallable


@contextlib.contextmanager
def override_registry(
    dispatch_callable: "_SingleDispatchCallable[Any]", cls: Type, mock: Mock
):
    """
    Helper to override a singledispatch function with a mock for testing.
    """
    original = dispatch_callable.registry[cls]
    dispatch_callable.register(cls, mock)
    try:
        yield mock
    finally:
        dispatch_callable.register(cls, original)


def test_routing_regex_event():
    """
    Ensure that the system properly calls the generate_stac_regexevent when regex-style
    events are provided.
    """
    mock_stac_dict = {"mock": "STAC Item"}
    mock_stac_item = MagicMock(spec=Item)
    mock_stac_item.to_dict.return_value = mock_stac_dict
    with override_registry(
        stac.generate_stac, events.RegexEvent, MagicMock(return_value=mock_stac_item)
    ), override_registry(
        stac.generate_stac, events.CmrEvent, MagicMock()
    ) as not_called_mock:
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
    assert "stac_item" in output
    created_stac_item = output["stac_item"]
    assert created_stac_item == mock_stac_dict
    assert not not_called_mock.call_count


def test_routing_cmr_event():
    """
    Ensure that the system properly calls the generate_stac_cmrevent when CMR-style
    events are provided.
    """
    mock_stac_dict = {"mock": "STAC Item"}
    mock_stac_item = MagicMock(spec=Item)
    mock_stac_item.to_dict.return_value = mock_stac_dict
    with override_registry(
        stac.generate_stac, events.CmrEvent, MagicMock(return_value=mock_stac_item)
    ), override_registry(
        stac.generate_stac, events.RegexEvent, MagicMock()
    ) as not_called_mock:
        output = handler.handler(
            {
                "collection": "test-collection",
                "s3_filename": "s3://test-bucket/delivery/BMHD_Maria_Stages/70001_BeforeMaria_Stage0_2017-07-21.tif",
                "granule_id": "test-granule",
            },
            None,
        )

    mock_stac_item.to_dict.assert_called_once_with()
    assert "stac_item" in output
    created_stac_item = output["stac_item"]
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


def test_foo():
    event = handler.handler(
        {
            "filename_regex": "^(.*)Combustion_Mobile.tif$",
            "datetime_range": None,
            "single_datetime": None,
            "start_datetime": "2012-01-01T00:00:00Z",
            "end_datetime": "2012-12-31T23:59:59Z",
            "properties": None,
            "collection": "EPA-annual-emissions_1A_Combustion_Mobile",
            "s3_filename": "s3://veda-data-store-staging/EIS/cog/EPA-inventory-2012/annual/EPA-annual-emissions_1A_Combustion_Mobile.tif",
            "href": "s3://veda-data-store-staging/EIS/cog/EPA-inventory-2012/annual/EPA-annual-emissions_1A_Combustion_Mobile.tif",
            "id": "EIS/cog/EPA-inventory-2012/annual/EPA-annual-emissions_1A_Combustion_Mobile.tif",
            "upload": False,
        },
        None,
    )
    output = stac.generate_stac(event)
    print(output)
