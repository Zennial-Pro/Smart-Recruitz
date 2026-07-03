"""Runtime feature flag registry."""

from app.config.settings import get_settings


def is_lms_integration_enabled() -> bool:
    return get_settings().feature_lms_integration


def is_ats_push_enabled() -> bool:
    return get_settings().feature_ats_push


def is_webhook_outbound_enabled() -> bool:
    return get_settings().feature_webhook_outbound
