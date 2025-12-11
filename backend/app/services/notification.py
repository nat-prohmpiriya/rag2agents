"""Notification service for managing user notifications."""

import logging
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

logger = logging.getLogger(__name__)


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


# ============================================================================
# Billing Notification Helpers
# ============================================================================


async def notify_quota_warning(
    db: AsyncSession,
    user_id: uuid.UUID,
    quota_type: str,
    used: int,
    limit: int,
    percentage: float,
) -> Notification | None:
    """
    Send notification when quota reaches 80% threshold.

    Args:
        db: Database session
        user_id: User to notify
        quota_type: Type of quota (tokens, documents, projects)
        used: Current usage
        limit: Total limit
        percentage: Usage percentage

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.BILLING, "in_app"
        ):
            return None

        quota_labels = {
            "tokens": "Token",
            "documents": "Document",
            "projects": "Project",
        }
        label = quota_labels.get(quota_type, quota_type.title())

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.QUOTA_WARNING,
            category=NotificationCategory.BILLING,
            title=f"{label} Quota Warning",
            message=f"You've used {percentage:.0f}% of your {quota_type} quota ({used:,} of {limit:,}). Consider upgrading your plan to avoid interruptions.",
            priority=NotificationPriority.HIGH,
            action_url="/profile",
            extra_data={
                "quota_type": quota_type,
                "used": used,
                "limit": limit,
                "percentage": percentage,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create quota warning notification: {e}")
        return None


async def notify_quota_exceeded(
    db: AsyncSession,
    user_id: uuid.UUID,
    quota_type: str,
    used: int,
    limit: int,
) -> Notification | None:
    """
    Send notification when quota is exceeded.

    Args:
        db: Database session
        user_id: User to notify
        quota_type: Type of quota (tokens, documents, projects)
        used: Current usage
        limit: Total limit

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.BILLING, "in_app"
        ):
            return None

        quota_labels = {
            "tokens": "Token",
            "documents": "Document",
            "projects": "Project",
        }
        label = quota_labels.get(quota_type, quota_type.title())

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.QUOTA_EXCEEDED,
            category=NotificationCategory.BILLING,
            title=f"{label} Quota Exceeded",
            message=f"You've exceeded your {quota_type} quota ({used:,} of {limit:,}). Please upgrade your plan to continue using this feature.",
            priority=NotificationPriority.CRITICAL,
            action_url="/profile",
            extra_data={
                "quota_type": quota_type,
                "used": used,
                "limit": limit,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create quota exceeded notification: {e}")
        return None


async def notify_payment_success(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: float,
    currency: str,
    invoice_number: str | None = None,
    plan_name: str | None = None,
) -> Notification | None:
    """
    Send notification when payment is successful.

    Args:
        db: Database session
        user_id: User to notify
        amount: Payment amount
        currency: Currency code
        invoice_number: Optional invoice number
        plan_name: Optional plan name

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.BILLING, "in_app"
        ):
            return None

        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "THB": "฿"}
        symbol = currency_symbols.get(currency.upper(), currency.upper() + " ")

        message = f"Payment of {symbol}{amount:.2f} was successful."
        if plan_name:
            message = f"Payment of {symbol}{amount:.2f} for {plan_name} plan was successful."
        if invoice_number:
            message += f" Invoice: {invoice_number}"

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.PAYMENT_SUCCESS,
            category=NotificationCategory.BILLING,
            title="Payment Successful",
            message=message,
            priority=NotificationPriority.LOW,
            action_url="/profile",
            extra_data={
                "amount": amount,
                "currency": currency,
                "invoice_number": invoice_number,
                "plan_name": plan_name,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create payment success notification: {e}")
        return None


async def notify_payment_failed(
    db: AsyncSession,
    user_id: uuid.UUID,
    amount: float,
    currency: str,
    reason: str | None = None,
) -> Notification | None:
    """
    Send notification when payment fails.

    Args:
        db: Database session
        user_id: User to notify
        amount: Payment amount
        currency: Currency code
        reason: Optional failure reason

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.BILLING, "in_app"
        ):
            return None

        currency_symbols = {"USD": "$", "EUR": "€", "GBP": "£", "THB": "฿"}
        symbol = currency_symbols.get(currency.upper(), currency.upper() + " ")

        message = f"Payment of {symbol}{amount:.2f} failed."
        if reason:
            message += f" Reason: {reason}"
        message += " Please update your payment method to avoid service interruption."

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.PAYMENT_FAILED,
            category=NotificationCategory.BILLING,
            title="Payment Failed",
            message=message,
            priority=NotificationPriority.CRITICAL,
            action_url="/profile",
            extra_data={
                "amount": amount,
                "currency": currency,
                "reason": reason,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create payment failed notification: {e}")
        return None


async def notify_subscription_renewed(
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_name: str,
    next_billing_date: datetime | None = None,
) -> Notification | None:
    """
    Send notification when subscription is renewed.

    Args:
        db: Database session
        user_id: User to notify
        plan_name: Name of the plan
        next_billing_date: Next billing date

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.BILLING, "in_app"
        ):
            return None

        message = f"Your {plan_name} subscription has been renewed."
        if next_billing_date:
            message += f" Next billing date: {next_billing_date.strftime('%B %d, %Y')}."

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.SUBSCRIPTION_RENEWED,
            category=NotificationCategory.BILLING,
            title="Subscription Renewed",
            message=message,
            priority=NotificationPriority.LOW,
            action_url="/profile",
            extra_data={
                "plan_name": plan_name,
                "next_billing_date": next_billing_date.isoformat() if next_billing_date else None,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create subscription renewed notification: {e}")
        return None


async def notify_subscription_expiring(
    db: AsyncSession,
    user_id: uuid.UUID,
    plan_name: str,
    expiry_date: datetime,
    days_remaining: int,
) -> Notification | None:
    """
    Send notification when subscription is about to expire.

    Args:
        db: Database session
        user_id: User to notify
        plan_name: Name of the plan
        expiry_date: Expiration date
        days_remaining: Days until expiration

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.BILLING, "in_app"
        ):
            return None

        if days_remaining <= 1:
            message = f"Your {plan_name} subscription expires tomorrow!"
            priority = NotificationPriority.CRITICAL
        elif days_remaining <= 3:
            message = f"Your {plan_name} subscription expires in {days_remaining} days."
            priority = NotificationPriority.HIGH
        else:
            message = f"Your {plan_name} subscription will expire on {expiry_date.strftime('%B %d, %Y')} ({days_remaining} days remaining)."
            priority = NotificationPriority.MEDIUM

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.SUBSCRIPTION_EXPIRING,
            category=NotificationCategory.BILLING,
            title="Subscription Expiring Soon",
            message=message,
            priority=priority,
            action_url="/profile",
            extra_data={
                "plan_name": plan_name,
                "expiry_date": expiry_date.isoformat(),
                "days_remaining": days_remaining,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create subscription expiring notification: {e}")
        return None


# ============================================================================
# Document Notification Helpers
# ============================================================================


async def notify_document_processed(
    db: AsyncSession,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    document_name: str,
    chunk_count: int,
) -> Notification | None:
    """
    Send notification when document processing completes successfully.

    Args:
        db: Database session
        user_id: User to notify
        document_id: Document ID
        document_name: Name of the document
        chunk_count: Number of chunks created

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.DOCUMENT, "in_app"
        ):
            return None

        message = f"Your document '{document_name}' has been processed successfully."
        if chunk_count > 0:
            message += f" {chunk_count} text chunks were created for search."

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.DOCUMENT_PROCESSED,
            category=NotificationCategory.DOCUMENT,
            title="Document Ready",
            message=message,
            priority=NotificationPriority.LOW,
            action_url=f"/documents/{document_id}",
            extra_data={
                "document_id": str(document_id),
                "document_name": document_name,
                "chunk_count": chunk_count,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create document processed notification: {e}")
        return None


async def notify_document_failed(
    db: AsyncSession,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
    document_name: str,
    error_message: str | None = None,
) -> Notification | None:
    """
    Send notification when document processing fails.

    Args:
        db: Database session
        user_id: User to notify
        document_id: Document ID
        document_name: Name of the document
        error_message: Error message describing the failure

    Returns:
        Created notification or None if preferences disabled
    """
    try:
        if not await should_send_notification(
            db, user_id, NotificationCategory.DOCUMENT, "in_app"
        ):
            return None

        message = f"Failed to process document '{document_name}'."
        if error_message:
            # Truncate long error messages
            truncated_error = error_message[:200] + "..." if len(error_message) > 200 else error_message
            message += f" Error: {truncated_error}"
        message += " Please try uploading again or contact support if the issue persists."

        return await create_notification(
            db=db,
            user_id=user_id,
            type=NotificationType.DOCUMENT_FAILED,
            category=NotificationCategory.DOCUMENT,
            title="Document Processing Failed",
            message=message,
            priority=NotificationPriority.HIGH,
            action_url=f"/documents/{document_id}",
            extra_data={
                "document_id": str(document_id),
                "document_name": document_name,
                "error_message": error_message,
            },
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to create document failed notification: {e}")
        return None
