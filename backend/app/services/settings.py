"""Settings service for managing application configuration."""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import traced
from app.models.setting import Setting, SettingCategory
from app.schemas.admin import (
    AllSettingsResponse,
    GeneralSettings,
    LiteLLMSettings,
    NotificationSettings,
    PaymentSettings,
)

logger = logging.getLogger(__name__)

# Default settings configuration
DEFAULT_SETTINGS: dict[str, dict[str, Any]] = {
    # General settings
    "site_name": {
        "value": "RAG Agent Platform",
        "category": SettingCategory.GENERAL.value,
        "description": "The name of the application",
        "is_secret": False,
    },
    "default_plan_id": {
        "value": None,
        "category": SettingCategory.GENERAL.value,
        "description": "Default plan ID for new users",
        "is_secret": False,
    },
    "trial_period_days": {
        "value": "14",
        "category": SettingCategory.GENERAL.value,
        "description": "Number of days for trial period",
        "is_secret": False,
    },
    "allow_registration": {
        "value": "true",
        "category": SettingCategory.GENERAL.value,
        "description": "Allow new user registration",
        "is_secret": False,
    },
    "require_email_verification": {
        "value": "true",
        "category": SettingCategory.GENERAL.value,
        "description": "Require email verification for new users",
        "is_secret": False,
    },
    # Payment settings
    "stripe_publishable_key": {
        "value": None,
        "category": SettingCategory.PAYMENT.value,
        "description": "Stripe publishable API key",
        "is_secret": False,
    },
    "stripe_secret_key": {
        "value": None,
        "category": SettingCategory.PAYMENT.value,
        "description": "Stripe secret API key",
        "is_secret": True,
    },
    "stripe_webhook_secret": {
        "value": None,
        "category": SettingCategory.PAYMENT.value,
        "description": "Stripe webhook signing secret",
        "is_secret": True,
    },
    "currency": {
        "value": "usd",
        "category": SettingCategory.PAYMENT.value,
        "description": "Default currency for payments",
        "is_secret": False,
    },
    "tax_rate_percent": {
        "value": "0.0",
        "category": SettingCategory.PAYMENT.value,
        "description": "Tax rate percentage",
        "is_secret": False,
    },
    # LiteLLM settings
    "litellm_proxy_url": {
        "value": None,
        "category": SettingCategory.LITELLM.value,
        "description": "LiteLLM proxy base URL",
        "is_secret": False,
    },
    "litellm_master_key": {
        "value": None,
        "category": SettingCategory.LITELLM.value,
        "description": "LiteLLM master API key",
        "is_secret": True,
    },
    "litellm_default_model": {
        "value": "gemini-2.0-flash",
        "category": SettingCategory.LITELLM.value,
        "description": "Default LLM model",
        "is_secret": False,
    },
    "litellm_fallback_model": {
        "value": None,
        "category": SettingCategory.LITELLM.value,
        "description": "Fallback LLM model if primary fails",
        "is_secret": False,
    },
    "litellm_request_timeout_seconds": {
        "value": "60",
        "category": SettingCategory.LITELLM.value,
        "description": "Request timeout in seconds",
        "is_secret": False,
    },
    # Notification settings
    "slack_webhook_url": {
        "value": None,
        "category": SettingCategory.NOTIFICATION.value,
        "description": "Slack webhook URL for notifications",
        "is_secret": True,
    },
    "email_enabled": {
        "value": "true",
        "category": SettingCategory.NOTIFICATION.value,
        "description": "Enable email notifications",
        "is_secret": False,
    },
    "email_from_name": {
        "value": "RAG Agent Platform",
        "category": SettingCategory.NOTIFICATION.value,
        "description": "Email sender name",
        "is_secret": False,
    },
    "email_from_address": {
        "value": None,
        "category": SettingCategory.NOTIFICATION.value,
        "description": "Email sender address",
        "is_secret": False,
    },
    "smtp_host": {
        "value": None,
        "category": SettingCategory.NOTIFICATION.value,
        "description": "SMTP server hostname",
        "is_secret": False,
    },
    "smtp_port": {
        "value": "587",
        "category": SettingCategory.NOTIFICATION.value,
        "description": "SMTP server port",
        "is_secret": False,
    },
    "smtp_username": {
        "value": None,
        "category": SettingCategory.NOTIFICATION.value,
        "description": "SMTP authentication username",
        "is_secret": False,
    },
    "smtp_password": {
        "value": None,
        "category": SettingCategory.NOTIFICATION.value,
        "description": "SMTP authentication password",
        "is_secret": True,
    },
    "smtp_use_tls": {
        "value": "true",
        "category": SettingCategory.NOTIFICATION.value,
        "description": "Use TLS for SMTP connection",
        "is_secret": False,
    },
}


def _mask_secret(value: str | None) -> str | None:
    """Mask a secret value for display."""
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def _parse_bool(value: str | None) -> bool:
    """Parse a string boolean value."""
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "on")


def _parse_int(value: str | None, default: int = 0) -> int:
    """Parse a string integer value."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_float(value: str | None, default: float = 0.0) -> float:
    """Parse a string float value."""
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@traced()
async def get_setting(db: AsyncSession, key: str) -> Setting | None:
    """Get a single setting by key."""
    result = await db.execute(
        select(Setting).where(Setting.key == key)
    )
    return result.scalar_one_or_none()


@traced()
async def get_setting_value(db: AsyncSession, key: str, default: str | None = None) -> str | None:
    """Get a setting value by key."""
    setting = await get_setting(db, key)
    if setting is None:
        return default
    return setting.value


@traced()
async def get_settings_by_category(db: AsyncSession, category: str) -> list[Setting]:
    """Get all settings for a category."""
    result = await db.execute(
        select(Setting)
        .where(Setting.category == category)
        .order_by(Setting.key)
    )
    return list(result.scalars().all())


@traced()
async def get_all_settings(db: AsyncSession) -> list[Setting]:
    """Get all settings."""
    result = await db.execute(
        select(Setting).order_by(Setting.category, Setting.key)
    )
    return list(result.scalars().all())


@traced()
async def create_setting(
    db: AsyncSession,
    key: str,
    value: str | None = None,
    value_json: dict | None = None,
    category: str = SettingCategory.GENERAL.value,
    description: str | None = None,
    is_secret: bool = False,
    is_editable: bool = True,
) -> Setting:
    """Create a new setting."""
    setting = Setting(
        key=key,
        value=value,
        value_json=value_json,
        category=category,
        description=description,
        is_secret=is_secret,
        is_editable=is_editable,
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting


@traced()
async def update_setting(
    db: AsyncSession,
    key: str,
    value: str | None = None,
    value_json: dict | None = None,
    description: str | None = None,
) -> Setting | None:
    """Update an existing setting."""
    setting = await get_setting(db, key)
    if setting is None:
        return None

    if not setting.is_editable:
        raise ValueError(f"Setting '{key}' is not editable")

    if value is not None:
        setting.value = value
    if value_json is not None:
        setting.value_json = value_json
    if description is not None:
        setting.description = description

    await db.commit()
    await db.refresh(setting)
    return setting


@traced()
async def upsert_setting(
    db: AsyncSession,
    key: str,
    value: str | None = None,
    value_json: dict | None = None,
    category: str | None = None,
    description: str | None = None,
    is_secret: bool | None = None,
) -> Setting:
    """Create or update a setting."""
    setting = await get_setting(db, key)

    if setting is None:
        # Create new setting
        default_config = DEFAULT_SETTINGS.get(key, {})
        setting = Setting(
            key=key,
            value=value,
            value_json=value_json,
            category=category or default_config.get("category", SettingCategory.GENERAL.value),
            description=description or default_config.get("description"),
            is_secret=is_secret if is_secret is not None else default_config.get("is_secret", False),
            is_editable=True,
        )
        db.add(setting)
    else:
        # Update existing setting
        if value is not None:
            setting.value = value
        if value_json is not None:
            setting.value_json = value_json
        if description is not None:
            setting.description = description

    await db.commit()
    await db.refresh(setting)
    return setting


@traced()
async def delete_setting(db: AsyncSession, key: str) -> bool:
    """Delete a setting."""
    setting = await get_setting(db, key)
    if setting is None:
        return False

    await db.delete(setting)
    await db.commit()
    return True


@traced()
async def initialize_default_settings(db: AsyncSession) -> int:
    """Initialize default settings if they don't exist."""
    count = 0
    for key, config in DEFAULT_SETTINGS.items():
        existing = await get_setting(db, key)
        if existing is None:
            await create_setting(
                db=db,
                key=key,
                value=config.get("value"),
                category=config.get("category", SettingCategory.GENERAL.value),
                description=config.get("description"),
                is_secret=config.get("is_secret", False),
                is_editable=True,
            )
            count += 1
    return count


@traced()
async def get_all_settings_structured(db: AsyncSession, mask_secrets: bool = True) -> AllSettingsResponse:
    """Get all settings as structured response for frontend."""
    settings = await get_all_settings(db)

    # Build a lookup dict
    settings_dict: dict[str, str | None] = {}
    for s in settings:
        if s.is_secret and mask_secrets:
            settings_dict[s.key] = _mask_secret(s.value)
        else:
            settings_dict[s.key] = s.value

    return AllSettingsResponse(
        general=GeneralSettings(
            site_name=settings_dict.get("site_name") or "RAG Agent Platform",
            default_plan_id=settings_dict.get("default_plan_id"),
            trial_period_days=_parse_int(settings_dict.get("trial_period_days"), 14),
            allow_registration=_parse_bool(settings_dict.get("allow_registration")),
            require_email_verification=_parse_bool(settings_dict.get("require_email_verification")),
        ),
        payment=PaymentSettings(
            stripe_publishable_key=settings_dict.get("stripe_publishable_key"),
            stripe_secret_key=settings_dict.get("stripe_secret_key"),
            stripe_webhook_secret=settings_dict.get("stripe_webhook_secret"),
            currency=settings_dict.get("currency") or "usd",
            tax_rate_percent=_parse_float(settings_dict.get("tax_rate_percent"), 0.0),
        ),
        litellm=LiteLLMSettings(
            proxy_url=settings_dict.get("litellm_proxy_url"),
            master_key=settings_dict.get("litellm_master_key"),
            default_model=settings_dict.get("litellm_default_model") or "gemini-2.0-flash",
            fallback_model=settings_dict.get("litellm_fallback_model"),
            request_timeout_seconds=_parse_int(settings_dict.get("litellm_request_timeout_seconds"), 60),
        ),
        notification=NotificationSettings(
            slack_webhook_url=settings_dict.get("slack_webhook_url"),
            email_enabled=_parse_bool(settings_dict.get("email_enabled")),
            email_from_name=settings_dict.get("email_from_name") or "RAG Agent Platform",
            email_from_address=settings_dict.get("email_from_address"),
            smtp_host=settings_dict.get("smtp_host"),
            smtp_port=_parse_int(settings_dict.get("smtp_port"), 587),
            smtp_username=settings_dict.get("smtp_username"),
            smtp_password=settings_dict.get("smtp_password"),
            smtp_use_tls=_parse_bool(settings_dict.get("smtp_use_tls")),
        ),
    )


@traced()
async def update_general_settings(db: AsyncSession, settings: GeneralSettings) -> None:
    """Update general settings."""
    await upsert_setting(db, "site_name", value=settings.site_name)
    await upsert_setting(db, "default_plan_id", value=settings.default_plan_id)
    await upsert_setting(db, "trial_period_days", value=str(settings.trial_period_days))
    await upsert_setting(db, "allow_registration", value=str(settings.allow_registration).lower())
    await upsert_setting(db, "require_email_verification", value=str(settings.require_email_verification).lower())


@traced()
async def update_payment_settings(db: AsyncSession, settings: PaymentSettings) -> None:
    """Update payment settings."""
    await upsert_setting(db, "stripe_publishable_key", value=settings.stripe_publishable_key)
    # Only update secrets if they're not masked
    if settings.stripe_secret_key and not settings.stripe_secret_key.startswith("*"):
        await upsert_setting(db, "stripe_secret_key", value=settings.stripe_secret_key)
    if settings.stripe_webhook_secret and not settings.stripe_webhook_secret.startswith("*"):
        await upsert_setting(db, "stripe_webhook_secret", value=settings.stripe_webhook_secret)
    await upsert_setting(db, "currency", value=settings.currency)
    await upsert_setting(db, "tax_rate_percent", value=str(settings.tax_rate_percent))


@traced()
async def update_litellm_settings(db: AsyncSession, settings: LiteLLMSettings) -> None:
    """Update LiteLLM settings."""
    await upsert_setting(db, "litellm_proxy_url", value=settings.proxy_url)
    # Only update secrets if they're not masked
    if settings.master_key and not settings.master_key.startswith("*"):
        await upsert_setting(db, "litellm_master_key", value=settings.master_key)
    await upsert_setting(db, "litellm_default_model", value=settings.default_model)
    await upsert_setting(db, "litellm_fallback_model", value=settings.fallback_model)
    await upsert_setting(db, "litellm_request_timeout_seconds", value=str(settings.request_timeout_seconds))


@traced()
async def update_notification_settings(db: AsyncSession, settings: NotificationSettings) -> None:
    """Update notification settings."""
    # Only update secrets if they're not masked
    if settings.slack_webhook_url and not settings.slack_webhook_url.startswith("*"):
        await upsert_setting(db, "slack_webhook_url", value=settings.slack_webhook_url)
    await upsert_setting(db, "email_enabled", value=str(settings.email_enabled).lower())
    await upsert_setting(db, "email_from_name", value=settings.email_from_name)
    await upsert_setting(db, "email_from_address", value=settings.email_from_address)
    await upsert_setting(db, "smtp_host", value=settings.smtp_host)
    await upsert_setting(db, "smtp_port", value=str(settings.smtp_port))
    await upsert_setting(db, "smtp_username", value=settings.smtp_username)
    if settings.smtp_password and not settings.smtp_password.startswith("*"):
        await upsert_setting(db, "smtp_password", value=settings.smtp_password)
    await upsert_setting(db, "smtp_use_tls", value=str(settings.smtp_use_tls).lower())
