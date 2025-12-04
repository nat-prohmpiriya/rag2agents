"""Notification service for managing user notifications."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry import traced
from app.models.notification import (
    Notification,
    NotificationCategory,
    NotificationPriority,
    NotificationType,
)
from app.models.notification_preference import (
    DEFAULT_CATEGORY_SETTINGS,
    NotificationPreference,
)
from app.schemas.notification import NotificationPreferenceUpdate


@traced()
async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    type: NotificationType,
    category: NotificationCategory,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.LOW,
    action_url: str | None = None,
    extra_data: dict | None = None,
    expires_at: datetime | None = None,
) -> Notification:
    """Create a single notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=type.value,
        category=category.value,
        title=title,
        message=message,
        priority=priority.value,
        action_url=action_url,
        extra_data=extra_data,
        expires_at=expires_at,
    )
    db.add(notification)
    await db.flush()
    await db.refresh(notification)
    return notification


@traced()
async def create_bulk_notifications(
    db: AsyncSession,
    user_ids: list[uuid.UUID],
    type: NotificationType,
    category: NotificationCategory,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.LOW,
    action_url: str | None = None,
    extra_data: dict | None = None,
    expires_at: datetime | None = None,
) -> int:
    """
    Create notifications for multiple users.

    Returns the number of notifications created.
    """
    notifications = [
        Notification(
            user_id=user_id,
            type=type.value,
            category=category.value,
            title=title,
            message=message,
            priority=priority.value,
            action_url=action_url,
            extra_data=extra_data,
            expires_at=expires_at,
        )
        for user_id in user_ids
    ]
    db.add_all(notifications)
    await db.flush()
    return len(notifications)


@traced()
async def get_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    unread_only: bool = False,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Notification], int]:
    """
    Get paginated notifications for a user.

    Returns a tuple of (notifications, total_count).
    """
    # Base query
    query = select(Notification).where(Notification.user_id == user_id)

    # Filter unread only
    if unread_only:
        query = query.where(Notification.read_at.is_(None))

    # Filter out expired notifications
    query = query.where(
        (Notification.expires_at.is_(None)) | (Notification.expires_at > func.now())
    )

    # Count total
    count_query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
        .where(
            (Notification.expires_at.is_(None)) | (Notification.expires_at > func.now())
        )
    )
    if unread_only:
        count_query = count_query.where(Notification.read_at.is_(None))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering (newest first)
    query = query.order_by(Notification.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    notifications = list(result.scalars().all())

    return notifications, total


@traced()
async def get_unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Get the count of unread notifications for badge display."""
    query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.read_at.is_(None))
        .where(
            (Notification.expires_at.is_(None)) | (Notification.expires_at > func.now())
        )
    )
    result = await db.execute(query)
    return result.scalar() or 0


@traced()
async def mark_as_read(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Notification | None:
    """
    Mark a single notification as read.

    Returns the updated notification or None if not found.
    """
    query = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        return None

    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        await db.flush()
        await db.refresh(notification)

    return notification


@traced()
async def mark_all_as_read(db: AsyncSession, user_id: uuid.UUID) -> int:
    """
    Mark all unread notifications as read for a user.

    Returns the number of notifications marked as read.
    """
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.read_at.is_(None))
        .values(read_at=datetime.utcnow())
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount


@traced()
async def delete_notification(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> bool:
    """
    Soft delete a notification by setting expires_at to now.

    Returns True if deleted, False if not found.
    """
    query = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        return False

    # Soft delete by setting expires_at to past
    notification.expires_at = datetime.utcnow() - timedelta(seconds=1)
    await db.flush()
    return True


@traced()
async def get_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> NotificationPreference:
    """
    Get notification preferences for a user.

    Creates default preferences if they don't exist.
    """
    query = select(NotificationPreference).where(
        NotificationPreference.user_id == user_id
    )
    result = await db.execute(query)
    preferences = result.scalar_one_or_none()

    if not preferences:
        # Create default preferences
        preferences = NotificationPreference(
            user_id=user_id,
            email_enabled=True,
            in_app_enabled=True,
            category_settings=DEFAULT_CATEGORY_SETTINGS,
        )
        db.add(preferences)
        await db.flush()
        await db.refresh(preferences)

    return preferences


@traced()
async def update_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: NotificationPreferenceUpdate,
) -> NotificationPreference:
    """Update notification preferences for a user."""
    # Get or create preferences
    preferences = await get_preferences(db, user_id)

    # Update fields that are provided
    if data.email_enabled is not None:
        preferences.email_enabled = data.email_enabled
    if data.in_app_enabled is not None:
        preferences.in_app_enabled = data.in_app_enabled
    if data.category_settings is not None:
        preferences.category_settings = data.category_settings
    if data.quiet_hours_start is not None:
        preferences.quiet_hours_start = data.quiet_hours_start
    if data.quiet_hours_end is not None:
        preferences.quiet_hours_end = data.quiet_hours_end

    await db.flush()
    await db.refresh(preferences)
    return preferences


@traced()
async def cleanup_expired(db: AsyncSession) -> int:
    """
    Delete expired notifications from the database.

    Returns the number of notifications deleted.
    """
    stmt = delete(Notification).where(
        Notification.expires_at.is_not(None),
        Notification.expires_at < func.now(),
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount


@traced()
async def should_send_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: NotificationCategory,
    channel: str = "in_app",
) -> bool:
    """
    Check if a notification should be sent based on user preferences.

    Args:
        db: Database session
        user_id: User ID to check
        category: Notification category
        channel: 'email' or 'in_app'

    Returns True if notification should be sent.
    """
    preferences = await get_preferences(db, user_id)

    # Check global toggle
    if channel == "email" and not preferences.email_enabled:
        return False
    if channel == "in_app" and not preferences.in_app_enabled:
        return False

    # Check category-specific settings
    category_settings = preferences.category_settings.get(category.value, {})
    return category_settings.get(channel, True)


def calculate_pages(total: int, per_page: int) -> int:
    """Calculate total number of pages."""
    return (total + per_page - 1) // per_page if total > 0 else 0
