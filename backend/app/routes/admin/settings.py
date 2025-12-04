"""Admin Settings API endpoints."""


from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_context
from app.core.dependencies import get_db, require_admin
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.admin import (
    AllSettingsResponse,
    AllSettingsUpdate,
    GeneralSettings,
    LiteLLMSettings,
    NotificationSettings,
    PaymentSettings,
    SettingResponse,
    SettingUpdate,
)
from app.schemas.base import BaseResponse, MessageResponse
from app.services import audit_log as audit_service
from app.services import settings as settings_service

router = APIRouter(prefix="/settings", tags=["admin-settings"])


@router.get("")
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[AllSettingsResponse]:
    """Get all settings structured for frontend (admin only).

    Returns settings grouped by category with secrets masked.
    """
    ctx = get_context()

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings,
    )


@router.put("")
async def update_all_settings(
    data: AllSettingsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BaseResponse[AllSettingsResponse]:
    """Update all settings at once (admin only).

    Updates settings for each category provided.
    Secrets that are masked (contain ***) will not be updated.
    """
    ctx = get_context()

    # Track which categories were updated for audit log
    updated_categories = []

    if data.general is not None:
        await settings_service.update_general_settings(db, data.general)
        updated_categories.append("general")

    if data.payment is not None:
        await settings_service.update_payment_settings(db, data.payment)
        updated_categories.append("payment")

    if data.litellm is not None:
        await settings_service.update_litellm_settings(db, data.litellm)
        updated_categories.append("litellm")

    if data.notification is not None:
        await settings_service.update_notification_settings(db, data.notification)
        updated_categories.append("notification")

    # Create audit log
    if updated_categories:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        await audit_service.create_audit_log(
            db=db,
            admin_id=admin.id,
            action=AuditAction.SETTINGS_UPDATE.value,
            description=f"Updated settings: {', '.join(updated_categories)}",
            target_type="settings",
            target_id=None,
            details={"categories": updated_categories},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    # Return updated settings
    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings,
    )


@router.get("/general")
async def get_general_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[GeneralSettings]:
    """Get general settings (admin only)."""
    ctx = get_context()

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.general,
    )


@router.put("/general")
async def update_general_settings(
    data: GeneralSettings,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BaseResponse[GeneralSettings]:
    """Update general settings (admin only)."""
    ctx = get_context()

    await settings_service.update_general_settings(db, data)

    # Audit log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_service.create_audit_log(
        db=db,
        admin_id=admin.id,
        action=AuditAction.SETTINGS_UPDATE.value,
        description="Updated general settings",
        target_type="settings",
        target_id=None,
        details={"category": "general"},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.general,
    )


@router.get("/payment")
async def get_payment_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[PaymentSettings]:
    """Get payment/Stripe settings (admin only)."""
    ctx = get_context()

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.payment,
    )


@router.put("/payment")
async def update_payment_settings(
    data: PaymentSettings,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BaseResponse[PaymentSettings]:
    """Update payment/Stripe settings (admin only)."""
    ctx = get_context()

    await settings_service.update_payment_settings(db, data)

    # Audit log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_service.create_audit_log(
        db=db,
        admin_id=admin.id,
        action=AuditAction.SETTINGS_UPDATE.value,
        description="Updated payment settings",
        target_type="settings",
        target_id=None,
        details={"category": "payment"},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.payment,
    )


@router.get("/litellm")
async def get_litellm_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[LiteLLMSettings]:
    """Get LiteLLM settings (admin only)."""
    ctx = get_context()

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.litellm,
    )


@router.put("/litellm")
async def update_litellm_settings(
    data: LiteLLMSettings,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BaseResponse[LiteLLMSettings]:
    """Update LiteLLM settings (admin only)."""
    ctx = get_context()

    await settings_service.update_litellm_settings(db, data)

    # Audit log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_service.create_audit_log(
        db=db,
        admin_id=admin.id,
        action=AuditAction.SETTINGS_UPDATE.value,
        description="Updated LiteLLM settings",
        target_type="settings",
        target_id=None,
        details={"category": "litellm"},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.litellm,
    )


@router.get("/notification")
async def get_notification_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[NotificationSettings]:
    """Get notification settings (admin only)."""
    ctx = get_context()

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.notification,
    )


@router.put("/notification")
async def update_notification_settings(
    data: NotificationSettings,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BaseResponse[NotificationSettings]:
    """Update notification settings (admin only)."""
    ctx = get_context()

    await settings_service.update_notification_settings(db, data)

    # Audit log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_service.create_audit_log(
        db=db,
        admin_id=admin.id,
        action=AuditAction.SETTINGS_UPDATE.value,
        description="Updated notification settings",
        target_type="settings",
        target_id=None,
        details={"category": "notification"},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    all_settings = await settings_service.get_all_settings_structured(db, mask_secrets=True)

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=all_settings.notification,
    )


@router.post("/initialize")
async def initialize_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BaseResponse[MessageResponse]:
    """Initialize default settings (admin only).

    Creates default settings if they don't exist.
    """
    ctx = get_context()

    count = await settings_service.initialize_default_settings(db)

    # Audit log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_service.create_audit_log(
        db=db,
        admin_id=admin.id,
        action=AuditAction.SYSTEM_CONFIG.value,
        description=f"Initialized {count} default settings",
        target_type="settings",
        target_id=None,
        details={"settings_created": count},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message=f"Initialized {count} default settings"),
    )


@router.get("/raw")
async def get_all_settings_raw(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[list[SettingResponse]]:
    """Get all settings as raw key-value pairs (admin only).

    Optionally filter by category.
    """
    ctx = get_context()

    if category:
        settings = await settings_service.get_settings_by_category(db, category)
    else:
        settings = await settings_service.get_all_settings(db)

    # Mask secrets
    settings_response = []
    for s in settings:
        setting_dict = {
            "id": s.id,
            "key": s.key,
            "value": settings_service._mask_secret(s.value) if s.is_secret else s.value,
            "value_json": s.value_json,
            "category": s.category,
            "description": s.description,
            "is_secret": s.is_secret,
            "is_editable": s.is_editable,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        settings_response.append(SettingResponse.model_validate(setting_dict))

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=settings_response,
    )


@router.put("/raw/{key}")
async def update_setting_raw(
    key: str,
    data: SettingUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> BaseResponse[SettingResponse]:
    """Update a single setting by key (admin only)."""
    ctx = get_context()

    setting = await settings_service.get_setting(db, key)
    if setting is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    if not setting.is_editable:
        raise HTTPException(status_code=400, detail=f"Setting '{key}' is not editable")

    # Don't update masked values
    value = data.value
    if value and setting.is_secret and value.startswith("*"):
        value = None

    setting = await settings_service.update_setting(
        db=db,
        key=key,
        value=value,
        value_json=data.value_json,
        description=data.description,
    )

    # Audit log
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await audit_service.create_audit_log(
        db=db,
        admin_id=admin.id,
        action=AuditAction.SETTINGS_UPDATE.value,
        description=f"Updated setting: {key}",
        target_type="setting",
        target_id=setting.id if setting else None,
        details={"key": key},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Mask secret in response
    setting_dict = {
        "id": setting.id,
        "key": setting.key,
        "value": settings_service._mask_secret(setting.value) if setting.is_secret else setting.value,
        "value_json": setting.value_json,
        "category": setting.category,
        "description": setting.description,
        "is_secret": setting.is_secret,
        "is_editable": setting.is_editable,
        "created_at": setting.created_at,
        "updated_at": setting.updated_at,
    }

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=SettingResponse.model_validate(setting_dict),
    )
