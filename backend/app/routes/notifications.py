"""Notification API endpoints for users."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_context
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.notification import (
    MarkAllAsReadResponse,
    MarkAsReadResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services import notification as notification_service
from app.services.notification_sse import notification_sse_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    page: int = 1,
    per_page: int = 20,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[NotificationListResponse]:
    """
    List notifications for the current user.

    Query parameters:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    - unread_only: Only return unread notifications (default: false)
    """
    ctx = get_context()

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    notifications, total = await notification_service.get_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only,
        page=page,
        per_page=per_page,
    )

    pages = notification_service.calculate_pages(total, per_page)

    items = [NotificationResponse.model_validate(n) for n in notifications]

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=NotificationListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        ),
    )


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[UnreadCountResponse]:
    """Get the count of unread notifications for badge display."""
    ctx = get_context()

    count = await notification_service.get_unread_count(
        db=db,
        user_id=current_user.id,
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=UnreadCountResponse(count=count),
    )


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[MarkAsReadResponse]:
    """Mark a single notification as read."""
    ctx = get_context()

    notification = await notification_service.mark_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MarkAsReadResponse(
            success=True,
            read_at=notification.read_at,
        ),
    )


@router.post("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[MarkAllAsReadResponse]:
    """Mark all notifications as read for the current user."""
    ctx = get_context()

    count = await notification_service.mark_all_as_read(
        db=db,
        user_id=current_user.id,
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MarkAllAsReadResponse(
            success=True,
            count=count,
        ),
    )


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[dict]:
    """Delete a notification (soft delete)."""
    ctx = get_context()

    deleted = await notification_service.delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data={"success": True, "message": "Notification deleted"},
    )


@router.get("/preferences")
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[NotificationPreferenceResponse]:
    """Get notification preferences for the current user."""
    ctx = get_context()

    preferences = await notification_service.get_preferences(
        db=db,
        user_id=current_user.id,
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=NotificationPreferenceResponse.model_validate(preferences),
    )


@router.put("/preferences")
async def update_preferences(
    data: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BaseResponse[NotificationPreferenceResponse]:
    """Update notification preferences for the current user."""
    ctx = get_context()

    preferences = await notification_service.update_preferences(
        db=db,
        user_id=current_user.id,
        data=data,
    )

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=NotificationPreferenceResponse.model_validate(preferences),
    )


@router.get("/stream")
async def notification_stream(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    SSE endpoint for real-time notification updates.

    Events:
    - connected: Initial connection with current unread count
    - unread_count: Updates to unread count
    - new_notification: New notification received
    - heartbeat: Keep-alive ping every 30 seconds
    """
    ctx = get_context()
    user_id = current_user.id

    async def event_generator():
        queue = await notification_sse_manager.connect(user_id)

        try:
            # Send initial unread count
            count = await notification_service.get_unread_count(db=db, user_id=user_id)
            yield f"event: connected\ndata: {json.dumps({'count': count})}\n\n"

            # Heartbeat interval (30 seconds)
            heartbeat_interval = 30

            while True:
                try:
                    # Wait for event or timeout for heartbeat
                    event = await asyncio.wait_for(
                        queue.get(), timeout=heartbeat_interval
                    )
                    yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"event: heartbeat\ndata: {json.dumps({'timestamp': asyncio.get_event_loop().time()})}\n\n"
                except asyncio.CancelledError:
                    break

        except Exception as e:
            logger.error(f"SSE error for user {user_id}: {e}")
        finally:
            await notification_sse_manager.disconnect(user_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "X-Trace-Id": ctx.trace_id,
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
