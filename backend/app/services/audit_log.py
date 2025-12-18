"""Audit log service for tracking admin actions."""

import logging
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.telemetry import traced
from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


@traced()
async def create_audit_log(
    db: AsyncSession,
    admin_id: uuid.UUID,
    action: str,
    description: str,
    target_type: str | None = None,
    target_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Create a new audit log entry."""
    audit_log = AuditLog(
        admin_id=admin_id,
        action=action,
        description=description,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit_log)
    await db.flush()
    return audit_log


@traced()
async def get_audit_logs(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    action: str | None = None,
    admin_id: uuid.UUID | None = None,
    target_type: str | None = None,
    target_id: uuid.UUID | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    """
    Get paginated audit logs with optional filters.

    Returns a tuple of (logs, total_count).
    """
    # Base query
    query = select(AuditLog).options(joinedload(AuditLog.admin))

    # Apply filters
    if action:
        query = query.where(AuditLog.action == action)
    if admin_id:
        query = query.where(AuditLog.admin_id == admin_id)
    if target_type:
        query = query.where(AuditLog.target_type == target_type)
    if target_id:
        query = query.where(AuditLog.target_id == target_id)
    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
    if search:
        query = query.where(AuditLog.description.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(AuditLog)
    if action:
        count_query = count_query.where(AuditLog.action == action)
    if admin_id:
        count_query = count_query.where(AuditLog.admin_id == admin_id)
    if target_type:
        count_query = count_query.where(AuditLog.target_type == target_type)
    if target_id:
        count_query = count_query.where(AuditLog.target_id == target_id)
    if start_date:
        count_query = count_query.where(AuditLog.created_at >= start_date)
    if end_date:
        count_query = count_query.where(AuditLog.created_at <= end_date)
    if search:
        count_query = count_query.where(AuditLog.description.ilike(f"%{search}%"))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    logs = result.scalars().unique().all()

    # Convert to dict format
    log_dicts = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "admin_id": log.admin_id,
            "admin": None,
            "action": log.action,
            "description": log.description,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at,
        }
        if log.admin:
            log_dict["admin"] = {
                "id": log.admin.id,
                "email": log.admin.email,
                "username": log.admin.username,
            }
        log_dicts.append(log_dict)

    return log_dicts, total


@traced()
async def get_audit_log_by_id(
    db: AsyncSession,
    log_id: uuid.UUID,
) -> dict | None:
    """Get a single audit log by ID."""
    query = (
        select(AuditLog)
        .options(joinedload(AuditLog.admin))
        .where(AuditLog.id == log_id)
    )
    result = await db.execute(query)
    log = result.scalar_one_or_none()

    if not log:
        return None

    log_dict = {
        "id": log.id,
        "admin_id": log.admin_id,
        "admin": None,
        "action": log.action,
        "description": log.description,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "user_agent": log.user_agent,
        "created_at": log.created_at,
    }
    if log.admin:
        log_dict["admin"] = {
            "id": log.admin.id,
            "email": log.admin.email,
            "username": log.admin.username,
        }

    return log_dict


@traced()
async def get_action_types() -> list[dict]:
    """Get all available action types."""
    from app.models.audit_log import AuditAction

    return [
        {"value": action.value, "label": action.value.replace("_", " ").title()}
        for action in AuditAction
    ]


@traced()
async def get_target_types() -> list[str]:
    """Get all available target types."""
    return ["user", "plan", "subscription", "invoice", "settings"]


@traced()
async def get_admins_for_filter(db: AsyncSession) -> list[dict]:
    """Get all admins for filter dropdown."""
    query = (
        select(User)
        .where(User.is_superuser == True)  # noqa: E712
        .order_by(User.email)
    )
    result = await db.execute(query)
    admins = result.scalars().all()

    return [
        {"id": admin.id, "email": admin.email, "username": admin.username}
        for admin in admins
    ]


def calculate_pages(total: int, per_page: int) -> int:
    """Calculate total number of pages."""
    return (total + per_page - 1) // per_page if total > 0 else 0
