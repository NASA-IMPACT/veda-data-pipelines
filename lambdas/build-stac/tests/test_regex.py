import pytest

from datetime import datetime

from utils import regex, events

default_event = {
    "collection": "some-collection",
}


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            # Single datetime - %Y-%m-%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2010-10-31_bar.tif",
                "datetime_range": None
            },
            (None, None, datetime(2010, 10, 31)),
        ),
        (
            # Single datetime - %Y%m%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_20051212_bar.tif",
                "datetime_range": None
            },
            (None, None, datetime(2005, 12, 12)),
        ),
        (
            # Single datetime - %Y%m
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_200507_bar.tif",
                "datetime_range": None
            },
            (None, None, datetime(2005, 7, 1)),
        ),
        (
            # Single datetime - %Y
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2012_bar.tif",
                "datetime_range": None
            },
            (None, None, datetime(2012, 1, 1)),
        ),
        (
            # Daterange - %Y-%m-%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2005-07-02_to_2006-09-29_bar.tif",
                "datetime_range": None
            },
            (datetime(2005, 7, 2), datetime(2006, 9, 29), None),
        ),
        (
            # Daterange - %Y%m%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_20050702_to_20060929_bar.tif",
                "datetime_range": None
            },
            (datetime(2005, 7, 2), datetime(2006, 9, 29), None),
        ),
        (
            # Daterange - %Y
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2005_2006_2007_bar.tif",
                "datetime_range": None
            },
            (datetime(2005, 1, 1), datetime(2007, 1, 1), None),
        ),
        (
            # Single date converted to month range - %Y-%m-%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2005-01-02.tif",
                "datetime_range": "month"
            },
            (datetime(2005, 1, 1), datetime(2005, 1, 31), None),
        ),
        (
            # Single date converted to month range - %Y%m%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2005-02-02.tif",
                "datetime_range": "month"
            },
            (datetime(2005, 2, 1), datetime(2005, 2, 28), None),
        ),
        (
            # Single date converted to month range - %Y%m
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_20050302_bar.tif",
                "datetime_range": "month"
            },
            (datetime(2005, 3, 1), datetime(2005, 3, 31), None),
        ),
        (
            # Single date converted to month range - %Y
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_20050402_bar.tif",
                "datetime_range": "month"
            },
            (datetime(2005, 4, 1), datetime(2005, 4, 30), None),
        ),
        (
            # Single date converted to year range - %Y-%m-%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2005-01-02.tif",
                "datetime_range": "year"
            },
            (datetime(2005, 1, 1), datetime(2005, 12, 31), None),
        ),
        (
            # Single date converted to year range - %Y%m%d
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_2005-02-02.tif",
                "datetime_range": "year"
            },
            (datetime(2005, 1, 1), datetime(2005, 12, 31), None),
        ),
        (
            # Single date converted to year range - %Y%m
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_20050302_bar.tif",
                "datetime_range": "year"
            },
            (datetime(2005, 1, 1), datetime(2005, 12, 31), None),
        ),
        (
            # Single date converted to year range - %Y
            {
                **default_event,
                "s3_filename": "s3://foo/bar/foo_20050402_bar.tif",
                "datetime_range": "year"
            },
            (datetime(2005, 1, 1), datetime(2005, 12, 31), None),
        ),
    ],
)
def test_date_extraction(test_input, expected):
    """
    Ensure dateranges are properly extracted from filenames.
    """
    assert regex.extract_dates(events.RegexEvent(**test_input)) == expected
