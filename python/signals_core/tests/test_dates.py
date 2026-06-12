"""Tests for signals_core.dates."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from signals_core.dates import (
    parse_published_at,
    parse_wayback_timestamp,
    to_utc,
    utcnow,
)


def test_utcnow_is_tz_aware_utc() -> None:
    now = utcnow()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_to_utc_attaches_tz_to_naive() -> None:
    naive = datetime(2024, 12, 12, 15, 30, 0)
    out = to_utc(naive)
    assert out.tzinfo is not None
    assert out.utcoffset() == timedelta(0)
    assert out.replace(tzinfo=None) == naive


def test_to_utc_converts_tz_aware() -> None:
    est = timezone(timedelta(hours=-5))
    aware = datetime(2024, 12, 12, 10, 30, 0, tzinfo=est)
    out = to_utc(aware)
    assert out.tzinfo is not None
    assert out.utcoffset() == timedelta(0)
    assert out.hour == 15
    assert out == aware


def test_parse_published_at_none_or_empty() -> None:
    assert parse_published_at(None) is None
    assert parse_published_at("") is None


def test_parse_published_at_naive_iso_treated_as_utc() -> None:
    out = parse_published_at("2024-12-12T10:30:00")
    assert out is not None
    assert out.utcoffset() == timedelta(0)
    assert out.hour == 10


def test_parse_published_at_aware_converted_to_utc() -> None:
    out = parse_published_at("2024-12-12T10:30:00-05:00")
    assert out is not None
    assert out.utcoffset() == timedelta(0)
    assert out.hour == 15


def test_parse_published_at_unparseable_returns_none() -> None:
    assert parse_published_at("not a date") is None
    assert parse_published_at("Thursday") is None


def test_parse_wayback_timestamp() -> None:
    out = parse_wayback_timestamp("20241212153000")
    assert out == datetime(2024, 12, 12, 15, 30, 0, tzinfo=UTC)


def test_parse_wayback_timestamp_invalid_raises() -> None:
    with pytest.raises(ValueError):
        parse_wayback_timestamp("not-a-timestamp")
