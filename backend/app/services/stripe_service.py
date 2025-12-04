"""Stripe Integration Service.

Handles payment processing with Stripe including:
- Checkout session creation
- Customer portal session
- Webhook event handling
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import stripe

from app.config import settings
from app.core.telemetry import traced
from app.models.invoice import Invoice, InvoiceStatus, PaymentMethod
from app.models.plan import Plan
from app.models.subscription import BillingInterval, Subscription, SubscriptionStatus
from app.models.user import User
from app.services import litellm_keys

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeError(Exception):
    """Exception for Stripe-related errors."""

    pass


# ============================================================================
# Checkout Session
# ============================================================================


@traced()
async def create_checkout_session(
    user: User,
    plan: Plan,
    billing_interval: str = "monthly",
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    """
    Create a Stripe checkout session for a subscription.

    Args:
        user: The user subscribing
        plan: The plan to subscribe to
        billing_interval: "monthly" or "yearly"
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if user cancels

    Returns:
        Dict with checkout session URL and ID
    """
    if not settings.stripe_secret_key:
        raise StripeError("Stripe is not configured")

    # Get the appropriate price ID
    if billing_interval == "yearly":
        price_id = plan.stripe_price_id_yearly
    else:
        price_id = plan.stripe_price_id_monthly

    if not price_id:
        raise StripeError(f"No Stripe price ID configured for plan {plan.name} ({billing_interval})")

    # Default URLs
    if not success_url:
        success_url = "http://localhost:5173/billing/success?session_id={CHECKOUT_SESSION_ID}"
    if not cancel_url:
        cancel_url = "http://localhost:5173/billing/cancel"

    try:
        # Check if user already has a Stripe customer ID
        customer_id = await get_or_create_customer(user)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
                "plan_id": str(plan.id),
                "plan_name": plan.name,
                "billing_interval": billing_interval,
            },
            subscription_data={
                "metadata": {
                    "user_id": str(user.id),
                    "plan_id": str(plan.id),
                    "plan_name": plan.name,
                    "billing_interval": billing_interval,
                }
            },
        )

        logger.info(f"Created checkout session {session.id} for user {user.id}")

        return {
            "session_id": session.id,
            "url": session.url,
        }

    except stripe.StripeError as e:
        logger.error(f"Stripe error creating checkout session: {e}")
        raise StripeError(f"Failed to create checkout session: {e}") from e


@traced()
async def get_or_create_customer(user: User) -> str:
    """
    Get existing Stripe customer or create new one.

    Args:
        user: The user

    Returns:
        Stripe customer ID
    """
    # Check if user already has a subscription with customer ID
    # This is a simplified check - in production you might want to
    # store customer_id directly on the user model
    try:
        # Search for existing customer by email
        customers = stripe.Customer.list(email=user.email, limit=1)
        if customers.data:
            return customers.data[0].id

        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username,
            metadata={
                "user_id": str(user.id),
                "username": user.username,
            },
        )

        logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
        return customer.id

    except stripe.StripeError as e:
        logger.error(f"Stripe error managing customer: {e}")
        raise StripeError(f"Failed to manage customer: {e}") from e


# ============================================================================
# Customer Portal
# ============================================================================


@traced()
async def create_customer_portal_session(
    user: User,
    return_url: str | None = None,
) -> dict[str, Any]:
    """
    Create a Stripe customer portal session for managing subscription.

    Args:
        user: The user
        return_url: URL to return to after portal session

    Returns:
        Dict with portal session URL
    """
    if not settings.stripe_secret_key:
        raise StripeError("Stripe is not configured")

    if not return_url:
        return_url = "http://localhost:5173/billing"

    try:
        customer_id = await get_or_create_customer(user)

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        logger.info(f"Created portal session for user {user.id}")

        return {
            "url": session.url,
        }

    except stripe.StripeError as e:
        logger.error(f"Stripe error creating portal session: {e}")
        raise StripeError(f"Failed to create portal session: {e}") from e


# ============================================================================
# Webhook Event Handlers
# ============================================================================


@traced()
async def verify_webhook_signature(
    payload: bytes,
    signature: str,
) -> stripe.Event:
    """
    Verify webhook signature and construct event.

    Args:
        payload: Raw request body
        signature: Stripe signature header

    Returns:
        Verified Stripe event
    """
    if not settings.stripe_webhook_secret:
        raise StripeError("Stripe webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
        )
        return event
    except stripe.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise StripeError("Invalid webhook signature") from e


@traced()
async def handle_subscription_created(
    db_session: Any,
    event: stripe.Event,
) -> Subscription | None:
    """
    Handle customer.subscription.created webhook.

    Creates a new subscription record and LiteLLM key.

    Args:
        db_session: Database session
        event: Stripe event

    Returns:
        Created Subscription or None
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    db: AsyncSession = db_session
    stripe_sub = event.data.object

    logger.info(f"Processing subscription created: {stripe_sub.id}")

    # Extract metadata
    metadata = stripe_sub.metadata
    user_id_str = metadata.get("user_id")
    plan_id_str = metadata.get("plan_id")
    billing_interval_str = metadata.get("billing_interval", "monthly")

    if not user_id_str or not plan_id_str:
        logger.error(f"Missing metadata in subscription {stripe_sub.id}")
        return None

    try:
        user_id = uuid.UUID(user_id_str)
        plan_id = uuid.UUID(plan_id_str)
    except ValueError as e:
        logger.error(f"Invalid UUID in metadata: {e}")
        return None

    # Get user and plan
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    plan_result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = plan_result.scalar_one_or_none()

    if not user or not plan:
        logger.error(f"User {user_id} or Plan {plan_id} not found")
        return None

    # Map Stripe status to our status
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "paused": SubscriptionStatus.PAUSED,
    }
    status = status_map.get(stripe_sub.status, SubscriptionStatus.ACTIVE)

    billing_interval = (
        BillingInterval.YEARLY if billing_interval_str == "yearly" else BillingInterval.MONTHLY
    )

    # Create LiteLLM key
    key_data = await litellm_keys.create_key_for_subscription(
        user_id=user.id,
        user_email=user.email,
        plan=plan,
        billing_interval=billing_interval_str,
    )

    # Create subscription record
    subscription = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status=status,
        billing_interval=billing_interval,
        start_date=datetime.fromtimestamp(stripe_sub.start_date, tz=UTC),
        current_period_start=datetime.fromtimestamp(
            stripe_sub.current_period_start, tz=UTC
        ) if stripe_sub.current_period_start else None,
        current_period_end=datetime.fromtimestamp(
            stripe_sub.current_period_end, tz=UTC
        ) if stripe_sub.current_period_end else None,
        trial_end_date=datetime.fromtimestamp(
            stripe_sub.trial_end, tz=UTC
        ) if stripe_sub.trial_end else None,
        stripe_subscription_id=stripe_sub.id,
        stripe_customer_id=stripe_sub.customer,
        litellm_key_id=key_data.get("key_id"),
    )

    db.add(subscription)

    # Update user tier
    user.tier = plan.plan_type.value
    db.add(user)

    await db.commit()
    await db.refresh(subscription)

    logger.info(f"Created subscription {subscription.id} for user {user.id}")
    return subscription


@traced()
async def handle_subscription_updated(
    db_session: Any,
    event: stripe.Event,
) -> Subscription | None:
    """
    Handle customer.subscription.updated webhook.

    Updates subscription record and LiteLLM key if plan changed.

    Args:
        db_session: Database session
        event: Stripe event

    Returns:
        Updated Subscription or None
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    db: AsyncSession = db_session
    stripe_sub = event.data.object

    logger.info(f"Processing subscription updated: {stripe_sub.id}")

    # Find existing subscription
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription not found for Stripe ID {stripe_sub.id}")
        return None

    # Map Stripe status
    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "paused": SubscriptionStatus.PAUSED,
    }
    new_status = status_map.get(stripe_sub.status, subscription.status)

    # Check if plan changed
    metadata = stripe_sub.metadata
    new_plan_id_str = metadata.get("plan_id")

    if new_plan_id_str:
        try:
            new_plan_id = uuid.UUID(new_plan_id_str)
            if new_plan_id != subscription.plan_id:
                # Plan changed - update LiteLLM key
                plan_result = await db.execute(select(Plan).where(Plan.id == new_plan_id))
                new_plan = plan_result.scalar_one_or_none()

                if new_plan and subscription.litellm_key_id:
                    billing_interval = metadata.get("billing_interval", "monthly")
                    await litellm_keys.update_key_for_plan_change(
                        key_id=subscription.litellm_key_id,
                        new_plan=new_plan,
                        billing_interval=billing_interval,
                    )
                    subscription.plan_id = new_plan_id

                    # Update user tier
                    user_result = await db.execute(
                        select(User).where(User.id == subscription.user_id)
                    )
                    user = user_result.scalar_one_or_none()
                    if user:
                        user.tier = new_plan.plan_type.value
                        db.add(user)

        except ValueError:
            pass

    # Update subscription fields
    subscription.status = new_status
    if stripe_sub.current_period_start:
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_sub.current_period_start, tz=UTC
        )
    if stripe_sub.current_period_end:
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_sub.current_period_end, tz=UTC
        )
    if stripe_sub.canceled_at:
        subscription.canceled_at = datetime.fromtimestamp(
            stripe_sub.canceled_at, tz=UTC
        )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    logger.info(f"Updated subscription {subscription.id}")
    return subscription


@traced()
async def handle_subscription_deleted(
    db_session: Any,
    event: stripe.Event,
) -> Subscription | None:
    """
    Handle customer.subscription.deleted webhook.

    Cancels subscription and disables LiteLLM key.

    Args:
        db_session: Database session
        event: Stripe event

    Returns:
        Canceled Subscription or None
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    db: AsyncSession = db_session
    stripe_sub = event.data.object

    logger.info(f"Processing subscription deleted: {stripe_sub.id}")

    # Find existing subscription
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub.id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription not found for Stripe ID {stripe_sub.id}")
        return None

    # Disable LiteLLM key
    if subscription.litellm_key_id:
        await litellm_keys.suspend_key_for_subscription(subscription.litellm_key_id)

    # Update subscription
    subscription.status = SubscriptionStatus.CANCELED
    subscription.canceled_at = datetime.now(UTC)
    subscription.end_date = datetime.now(UTC)

    # Update user tier to free
    user_result = await db.execute(select(User).where(User.id == subscription.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.tier = "free"
        db.add(user)

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    logger.info(f"Canceled subscription {subscription.id}")
    return subscription


@traced()
async def handle_invoice_paid(
    db_session: Any,
    event: stripe.Event,
) -> Invoice | None:
    """
    Handle invoice.paid webhook.

    Records the paid invoice and resets budget if new billing period.

    Args:
        db_session: Database session
        event: Stripe event

    Returns:
        Created Invoice or None
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    db: AsyncSession = db_session
    stripe_invoice = event.data.object

    logger.info(f"Processing invoice paid: {stripe_invoice.id}")

    # Check if invoice already recorded
    existing = await db.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == stripe_invoice.id)
    )
    if existing.scalar_one_or_none():
        logger.info(f"Invoice {stripe_invoice.id} already recorded")
        return None

    # Find subscription
    subscription = None
    if stripe_invoice.subscription:
        sub_result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_invoice.subscription
            )
        )
        subscription = sub_result.scalar_one_or_none()

    # Find user by customer ID
    customer_id = stripe_invoice.customer
    user = None
    if subscription:
        user_result = await db.execute(
            select(User).where(User.id == subscription.user_id)
        )
        user = user_result.scalar_one_or_none()
    else:
        # Try to find by customer ID in subscriptions
        sub_result = await db.execute(
            select(Subscription).where(Subscription.stripe_customer_id == customer_id)
        )
        sub = sub_result.scalar_one_or_none()
        if sub:
            user_result = await db.execute(select(User).where(User.id == sub.user_id))
            user = user_result.scalar_one_or_none()

    if not user:
        logger.warning(f"User not found for invoice {stripe_invoice.id}")
        return None

    # Generate invoice number
    invoice_count = await db.execute(
        select(Invoice).where(Invoice.user_id == user.id)
    )
    count = len(invoice_count.scalars().all())
    invoice_number = f"INV-{user.id.hex[:8].upper()}-{count + 1:04d}"

    # Create invoice record
    invoice = Invoice(
        user_id=user.id,
        subscription_id=subscription.id if subscription else None,
        invoice_number=invoice_number,
        status=InvoiceStatus.PAID,
        description=f"Subscription payment - {stripe_invoice.lines.data[0].description if stripe_invoice.lines.data else 'Subscription'}",
        subtotal=stripe_invoice.subtotal / 100,  # Convert from cents
        tax=stripe_invoice.tax / 100 if stripe_invoice.tax else 0,
        discount=stripe_invoice.total_discount_amounts[0].amount / 100 if stripe_invoice.total_discount_amounts else 0,
        total=stripe_invoice.total / 100,
        amount_paid=stripe_invoice.amount_paid / 100,
        amount_due=stripe_invoice.amount_remaining / 100,
        currency=stripe_invoice.currency.upper(),
        invoice_date=datetime.fromtimestamp(stripe_invoice.created, tz=UTC),
        due_date=datetime.fromtimestamp(stripe_invoice.due_date, tz=UTC) if stripe_invoice.due_date else None,
        paid_at=datetime.fromtimestamp(stripe_invoice.status_transitions.paid_at, tz=UTC) if stripe_invoice.status_transitions and stripe_invoice.status_transitions.paid_at else datetime.now(UTC),
        period_start=datetime.fromtimestamp(stripe_invoice.period_start, tz=UTC) if stripe_invoice.period_start else None,
        period_end=datetime.fromtimestamp(stripe_invoice.period_end, tz=UTC) if stripe_invoice.period_end else None,
        payment_method=PaymentMethod.CARD,
        stripe_invoice_id=stripe_invoice.id,
        stripe_payment_intent_id=stripe_invoice.payment_intent,
        stripe_hosted_invoice_url=stripe_invoice.hosted_invoice_url,
        stripe_invoice_pdf=stripe_invoice.invoice_pdf,
        line_items=[
            {
                "description": line.description,
                "amount": line.amount / 100,
                "quantity": line.quantity,
            }
            for line in stripe_invoice.lines.data
        ] if stripe_invoice.lines.data else None,
    )

    db.add(invoice)

    # Reset LiteLLM key budget for new billing period
    if subscription and subscription.litellm_key_id:
        await litellm_keys.reset_key_budget(subscription.litellm_key_id)
        logger.info(f"Reset budget for key {subscription.litellm_key_id}")

    await db.commit()
    await db.refresh(invoice)

    logger.info(f"Recorded invoice {invoice.invoice_number} for user {user.id}")
    return invoice


@traced()
async def handle_invoice_payment_failed(
    db_session: Any,
    event: stripe.Event,
) -> None:
    """
    Handle invoice.payment_failed webhook.

    Updates subscription status to past_due.

    Args:
        db_session: Database session
        event: Stripe event
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    db: AsyncSession = db_session
    stripe_invoice = event.data.object

    logger.warning(f"Processing invoice payment failed: {stripe_invoice.id}")

    if not stripe_invoice.subscription:
        return

    # Find subscription
    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_invoice.subscription
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.status = SubscriptionStatus.PAST_DUE
        db.add(subscription)
        await db.commit()
        logger.info(f"Marked subscription {subscription.id} as past_due")


# ============================================================================
# Webhook Dispatcher
# ============================================================================


WEBHOOK_HANDLERS = {
    "customer.subscription.created": handle_subscription_created,
    "customer.subscription.updated": handle_subscription_updated,
    "customer.subscription.deleted": handle_subscription_deleted,
    "invoice.paid": handle_invoice_paid,
    "invoice.payment_failed": handle_invoice_payment_failed,
}


@traced()
async def process_webhook_event(
    db_session: Any,
    event: stripe.Event,
) -> Any:
    """
    Process a verified Stripe webhook event.

    Args:
        db_session: Database session
        event: Verified Stripe event

    Returns:
        Result from handler or None
    """
    event_type = event.type
    handler = WEBHOOK_HANDLERS.get(event_type)

    if handler:
        logger.info(f"Processing webhook event: {event_type}")
        return await handler(db_session, event)
    else:
        logger.debug(f"Unhandled webhook event type: {event_type}")
        return None
