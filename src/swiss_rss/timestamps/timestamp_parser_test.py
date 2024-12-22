from datetime import datetime, timezone
from .timestamp_parser import parse_date


def test_parse_date_rfc2822():
    assert parse_date("Sat, 03 Jun 2023 10:00:00 GMT") == datetime(
        2023, 6, 3, 10, 0, tzinfo=timezone.utc
    )


def test_parse_date_iso8601():
    assert parse_date("2023-06-03T10:00:00Z") == datetime(
        2023, 6, 3, 10, 0, tzinfo=timezone.utc
    )


def test_parse_date_invalid():
    assert parse_date("Invalid Date") is None


def test_parse_date_none():
    assert parse_date(None) is None


def test_parse_date_empty_string():
    assert parse_date("") is None
