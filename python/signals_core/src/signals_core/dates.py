"""Date and time helpers shared across TELL adapters.

The adapters that feed the pipeline accept timestamps from several shapes of
source: trafilatura-extracted ISO 8601 strings with or without timezone,
Wayback snapshot timestamps in the compact ``YYYYMMDDHHMMSS`` form, and
``datetime.now()`` calls that need a UTC tzinfo. The same five-line
"parse, then normalize to UTC, then swallow ValueError" block appeared in
every adapter. These helpers replace it.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware UTC now.

    Equivalent to ``datetime.now(timezone.utc)``. Named explicitly so adapter
    code reads as intent (we always want a tz-aware UTC instant) rather than
    a reminder to pass the right argument every call.
    """
    return datetime.now(UTC)


def to_utc(value: datetime) -> datetime:
    """Return ``value`` as a tz-aware UTC datetime.

    If ``value`` is naive, it is assumed to already be in UTC and a UTC
    tzinfo is attached with ``replace``. If it is tz-aware, the instant is
    converted with ``astimezone``. The two branches are meaningfully
    different: ``replace`` preserves the clock time; ``astimezone`` does
    not. Using ``replace`` on a tz-aware datetime would silently shift the
    instant, which is the bug this helper is designed to rule out.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def parse_published_at(raw: str | None) -> datetime | None:
    """Parse a published_at string into a UTC datetime.

    Accepts any ISO 8601 string ``datetime.fromisoformat`` can read (3.11+
    handles most real-world shapes including the trailing ``Z``). Returns
    ``None`` if ``raw`` is falsy or unparseable. Tz-aware inputs are
    converted to UTC; naive inputs are assumed UTC and annotated.
    """
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return to_utc(parsed)


def parse_wayback_timestamp(ts: str) -> datetime:
    """Parse a Wayback Machine timestamp into a UTC datetime.

    The Wayback CDX API emits 14-digit ``YYYYMMDDHHMMSS`` strings in UTC.
    """
    return datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
