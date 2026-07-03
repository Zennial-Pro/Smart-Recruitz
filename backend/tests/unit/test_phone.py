"""Unit tests for phone-number normalization (app/utils/phone.py)."""

import pytest

from app.utils.phone import canonical_phone, to_e164


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("9014583641", "+919014583641"),
        ("09014583641", "+919014583641"),
        ("+91 90145 83641", "+919014583641"),
        ("+919014583641", "+919014583641"),
        ("919014583641", "+919014583641"),
        ("90145-83641", "+919014583641"),
    ],
)
def test_to_e164_indian_variants(raw, expected):
    assert to_e164(raw) == expected


def test_to_e164_empty_raises():
    with pytest.raises(ValueError):
        to_e164("")


@pytest.mark.parametrize(
    "raw,country_code,expected",
    [
        ("9014583641", None, "9014583641"),
        ("09014583641", None, "9014583641"),
        ("+91 90145 83641", None, "9014583641"),
        ("919014583641", None, "9014583641"),
        ("+919014583641", "91", "9014583641"),
        ("9014583641", "91", "9014583641"),
    ],
)
def test_canonical_phone_collapses_to_subscriber(raw, country_code, expected):
    assert canonical_phone(raw, country_code) == expected


def test_canonical_phone_matches_across_formats():
    """All of these must collapse to the same key so DB phone == webhook phone."""
    forms = ["9014583641", "09014583641", "+91 9014583641", "919014583641"]
    canon = {canonical_phone(f) for f in forms}
    assert len(canon) == 1


def test_canonical_phone_empty():
    assert canonical_phone("") == ""
    assert canonical_phone(None) == ""
