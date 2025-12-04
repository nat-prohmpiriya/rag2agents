"""Admin User Management API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import get_context
from app.core.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.admin import (
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
    BulkActionResponse,
    BulkUserAction,
    ChangeUserPlanRequest,
    SuspendUserRequest,
    UserActionResult,
)
from app.schemas.base import BaseResponse, MessageResponse
from app.services import admin_users as user_service

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.get("")
async def list_users(
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    plan: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[AdminUserListResponse]:
    """List all users with subscription and usage details (admin only)."""
    ctx = get_context()

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    users, total = await user_service.get_users_with_details(
        db=db,
        page=page,
        per_page=per_page,
        search=search,
        plan_filter=plan,
        status_filter=status,
    )

    pages = user_service.calculate_pages(total, per_page)

    items = [AdminUserResponse(**user) for user in users]

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=AdminUserListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        ),
    )


@router.get("/{user_id}")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[AdminUserResponse]:
    """Get a user by ID (admin only)."""
    ctx = get_context()

    users, _ = await user_service.get_users_with_details(
        db=db,
        page=1,
        per_page=1,
        search=str(user_id),
    )

    if not users:
        raise HTTPException(status_code=404, detail="User not found")

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=AdminUserResponse(**users[0]),
    )


@router.put("/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[MessageResponse]:
    """Update a user (admin only)."""
    ctx = get_context()

    user = await user_service.update_user(db=db, user_id=user_id, data=data)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.commit()

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="User updated successfully"),
    )


@router.post("/{user_id}/change-plan")
async def change_user_plan(
    user_id: uuid.UUID,
    data: ChangeUserPlanRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[MessageResponse]:
    """Change a user's subscription plan (admin only)."""
    ctx = get_context()

    subscription = await user_service.change_user_plan(
        db=db,
        user_id=user_id,
        plan_id=data.plan_id,
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="User or plan not found")

    await db.commit()

    # TODO: Sync with LiteLLM

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="User plan changed successfully"),
    )


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: uuid.UUID,
    data: SuspendUserRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[MessageResponse]:
    """Suspend a user account (admin only)."""
    ctx = get_context()

    reason = data.reason if data else None
    user = await user_service.suspend_user(db=db, user_id=user_id, reason=reason)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.commit()

    # TODO: Revoke LiteLLM key

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="User suspended successfully"),
    )


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[MessageResponse]:
    """Activate a suspended user account (admin only)."""
    ctx = get_context()

    user = await user_service.activate_user(db=db, user_id=user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.commit()

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="User activated successfully"),
    )


@router.post("/{user_id}/ban")
async def ban_user(
    user_id: uuid.UUID,
    data: SuspendUserRequest | None = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[MessageResponse]:
    """Ban a user account (admin only)."""
    ctx = get_context()

    reason = data.reason if data else None
    user = await user_service.ban_user(db=db, user_id=user_id, reason=reason)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.commit()

    # TODO: Revoke LiteLLM key

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="User banned successfully"),
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[MessageResponse]:
    """Delete a user and all their data (admin only)."""
    ctx = get_context()

    deleted = await user_service.delete_user(db=db, user_id=user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    await db.commit()

    # TODO: Delete LiteLLM key

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=MessageResponse(message="User deleted successfully"),
    )


@router.post("/bulk-action")
async def bulk_user_action(
    data: BulkUserAction,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> BaseResponse[BulkActionResponse]:
    """Perform bulk actions on multiple users (admin only)."""
    ctx = get_context()

    results: list[dict] = []

    if data.action == "change_plan":
        if not data.plan_id:
            raise HTTPException(
                status_code=400,
                detail="plan_id is required for change_plan action",
            )
        results = await user_service.bulk_change_plan(
            db=db,
            user_ids=data.user_ids,
            plan_id=data.plan_id,
        )
    elif data.action == "suspend":
        results = await user_service.bulk_suspend(
            db=db,
            user_ids=data.user_ids,
        )
    elif data.action == "activate":
        results = await user_service.bulk_activate(
            db=db,
            user_ids=data.user_ids,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action: {data.action}",
        )

    await db.commit()

    action_results = [UserActionResult(**r) for r in results]
    success_count = sum(1 for r in action_results if r.success)
    failure_count = len(action_results) - success_count

    return BaseResponse(
        trace_id=ctx.trace_id,
        data=BulkActionResponse(
            results=action_results,
            success_count=success_count,
            failure_count=failure_count,
        ),
    )
