"""Phone-number normalization for outbound voice calls.

Two needs, two functions:

- ``to_e164`` — format a stored candidate phone into the ``+<cc><number>`` form
  the Zingaro ``POST /v1/calls`` API expects.
- ``canonical_phone`` — reduce any phone (DB value, or the ``phone`` the pre-call
  webhook hands us) to a bare digit string so the two can be compared for
  equality regardless of how each was originally entered.

``CandidateMain.phone`` is free-form ``String(50)`` (the register validator only
checks 10–15 digits), and the pre-call webhook's *only* identifier is the phone
number — so canonicalizing both sides on read is the only reliable match.

Defaults assume Indian numbers (country code 91), matching the platform's own
sample webhook normalization.
"""

from __future__ import annotations

import re

DEFAULT_COUNTRY_CODE = "91"
_NON_DIGITS = re.compile(r"\D")


def _digits_only(raw: str) -> str:
    """Strip everything that isn't a digit."""
    return _NON_DIGITS.sub("", raw or "")


def canonical_phone(raw: str, country_code: str | None = None) -> str:
    """Reduce a phone number to its bare subscriber digits for equality matching.

    Strips formatting, a leading trunk ``0``, and a leading country code so that
    ``+91 90145 83641``, ``09014583641`` and ``9014583641`` all canonicalize to
    ``9014583641``.

    ``country_code`` (e.g. the webhook's ``country_code`` field) is stripped too
    when present, in addition to the default ``91``.
    """
    digits = _digits_only(raw)
    if not digits:
        return ""

    # Drop a single leading trunk zero (Indian domestic prefix): 09014583641 -> 9014583641
    if digits.startswith("0"):
        digits = digits.lstrip("0")

    # Strip an explicitly supplied country code if the number still leads with it.
    cc = _digits_only(country_code) if country_code else ""
    if cc and digits.startswith(cc) and len(digits) > len(cc) + 6:
        digits = digits[len(cc):]

    # Strip the default country code (91) when the result is longer than a local
    # 10-digit subscriber number (i.e. 91 + 10 digits = 12).
    if (
        digits.startswith(DEFAULT_COUNTRY_CODE)
        and len(digits) > 10
        and len(digits) - len(DEFAULT_COUNTRY_CODE) >= 10
    ):
        digits = digits[len(DEFAULT_COUNTRY_CODE):]

    return digits


def to_e164(raw: str, default_country_code: str = DEFAULT_COUNTRY_CODE) -> str:
    """Format a stored phone into E.164 (``+<cc><subscriber>``).

    Examples (default cc 91):
        ``9014583641``      -> ``+919014583641``
        ``09014583641``     -> ``+919014583641``
        ``+91 90145 83641`` -> ``+919014583641``
        ``919014583641``    -> ``+919014583641``
    """
    digits = _digits_only(raw)
    if not digits:
        raise ValueError("phone number is empty")

    if digits.startswith("0"):
        digits = digits.lstrip("0")

    # Already includes the country code (e.g. 12 digits starting with 91).
    if digits.startswith(default_country_code) and len(digits) > 10:
        return f"+{digits}"

    # Bare local subscriber number — prepend the default country code.
    if len(digits) == 10:
        return f"+{default_country_code}{digits}"

    # Anything else: assume it's already a full international number.
    return f"+{digits}"
