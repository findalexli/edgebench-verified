# Minimal Target 1 overlay (schemathesis.specs.openapi.headers) for the v4.14.3 starter.
# Written independently by the EBV re-verification reviewer. NOT a full task solution.
# EBV_DATE_VARIANT selects the http_date_values implementation.
from __future__ import annotations

import datetime as _dt
import os

from hypothesis import strategies as st

KNOWN_HEADER_FORMATS = {
    "if-match": "_if_match_header",
    "if-none-match": "_if_match_header",
    "if-modified-since": "_http_date_header",
    "if-unmodified-since": "_http_date_header",
    "range": "_range_header",
}

_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_VARIANT = os.environ.get("EBV_DATE_VARIANT", "correct")


def if_match_values():
    tag = st.text(alphabet="abcdef0123456789", min_size=1, max_size=8)
    etag = st.one_of(tag.map(lambda t: f'"{t}"'), tag.map(lambda t: f'W/"{t}"'))
    return st.one_of(st.just("*"), st.lists(etag, min_size=1, max_size=3).map(", ".join))


def _fmt(dt):
    # Locale-independent IMF-fixdate.
    return f"{_DAYS[dt.weekday()]}, {dt.day:02d} {_MONTHS[dt.month - 1]} {dt.year:04d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} GMT"


def http_date_values():
    if _VARIANT == "correct":
        # Real datetimes -> always a real Gregorian date, matching weekday, hour <= 23.
        return st.datetimes(min_value=_dt.datetime(1970, 1, 1), max_value=_dt.datetime(2100, 12, 31)).map(_fmt)
    if _VARIANT == "independent_fields":
        # Plausibly-wrong: each field drawn independently (a natural "grammar-driven" generator).
        # Produces 31 Apr / 30 Feb, weekday not implied by date, but hour within 00-23.
        return st.builds(
            lambda dn, d, m, y, h, mi, s: f"{dn}, {d:02d} {m} {y:04d} {h:02d}:{mi:02d}:{s:02d} GMT",
            st.sampled_from(_DAYS), st.integers(1, 31), st.sampled_from(_MONTHS),
            st.integers(1970, 2100), st.integers(0, 23), st.integers(0, 59), st.integers(0, 59),
        )
    if _VARIANT == "off_by_one_clock":
        # Plausibly-wrong: inclusive 24/60 bounds on the clock (hour 24, minute 60).
        return st.builds(
            lambda dt, h, mi: _fmt(dt)[:17] + f"{h:02d}:{mi:02d}:00 GMT",
            st.datetimes(min_value=_dt.datetime(1970, 1, 1), max_value=_dt.datetime(2100, 12, 31)),
            st.integers(0, 24), st.integers(0, 60),
        )
    if _VARIANT == "garbage_shape":
        # Clearly-wrong control that still matches the original shape regex: \w{3} accepts any word chars.
        return st.builds(
            lambda a, b: f"{a}, 99 {b} 0000 99:99:99 GMT",
            st.text(alphabet="XYZxyz_9", min_size=3, max_size=3), st.text(alphabet="QRSqrs_8", min_size=3, max_size=3),
        )
    if _VARIANT == "rfc850":
        # Clearly-wrong control (wrong format): obsolete RFC 850 form.
        return st.datetimes(min_value=_dt.datetime(1970, 1, 1), max_value=_dt.datetime(2100, 12, 31)).map(
            lambda dt: dt.strftime("%A, %d-%b-%y %H:%M:%S GMT"))
    raise ValueError(_VARIANT)


def _spec():
    pos = st.integers(0, 10_000)
    int_range = st.tuples(pos, pos).map(lambda t: f"{min(t)}-{max(t)}")
    return st.one_of(int_range, pos.map(lambda n: f"-{n}"), pos.map(lambda n: f"{n}-"))


def range_values():
    return st.lists(_spec(), min_size=1, max_size=3).map(lambda xs: "bytes=" + ",".join(xs))


def range_slightly_invalid_values():
    pos = st.integers(0, 10_000)
    inverted = st.tuples(pos, pos).filter(lambda t: t[0] != t[1]).map(lambda t: f"bytes={max(t)}-{min(t)}")
    return st.one_of(inverted, pos.map(lambda n: f"bytes=-1-{n}"), _spec().map(lambda s: f"invalid={s}"), st.just("bytes="))


def get_header_format_strategies(mode):
    from schemathesis.generation import GenerationMode

    if mode == GenerationMode.POSITIVE:
        rng = range_values()
    else:
        rand = st.text(alphabet="abcXYZ012 ", min_size=1, max_size=10).filter(
            lambda v: not v.startswith("bytes=") and not v.startswith("invalid="))
        rng = st.one_of(range_values(), range_slightly_invalid_values(), rand)
    return {"_if_match_header": if_match_values(), "_http_date_header": http_date_values(), "_range_header": rng}
