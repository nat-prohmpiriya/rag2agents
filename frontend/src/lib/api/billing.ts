/**
 * Billing API client
 */

import { fetchApi } from './client';

// Types
export interface BillingPlan {
	id: string;
	name: string;
	display_name: string;
	description: string | null;
	plan_type: 'free' | 'starter' | 'pro' | 'business' | 'enterprise';
	price_monthly: number;
	price_yearly: number | null;
	currency: string;
	tokens_per_month: number;
	requests_per_month: number;
	credits_per_month: number;
	requests_per_minute: number;
	requests_per_day: number;
	max_documents: number;
	max_projects: number;
	max_agents: number;
	allowed_models: string[];
	features: Record<string, unknown> | null;
}

export interface CheckoutRequest {
	plan_id: string;
	billing_interval: 'monthly' | 'yearly';
	success_url?: string;
	cancel_url?: string;
}

export interface CheckoutResponse {
	session_id: string;
	url: string;
}

export interface PortalResponse {
	url: string;
}

// API Functions

/**
 * Get all available billing plans
 */
export async function getPlans(): Promise<BillingPlan[]> {
	return fetchApi<BillingPlan[]>('/billing/plans');
}

/**
 * Create a Stripe checkout session for subscribing to a plan
 */
export async function createCheckout(request: CheckoutRequest): Promise<CheckoutResponse> {
	return fetchApi<CheckoutResponse>('/billing/checkout', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}

/**
 * Create a Stripe customer portal session for managing subscription
 */
export async function createPortalSession(returnUrl?: string): Promise<PortalResponse> {
	return fetchApi<PortalResponse>('/billing/portal', {
		method: 'POST',
		body: JSON.stringify({ return_url: returnUrl })
	});
}

// User subscription types
export interface UserSubscription {
	id: string;
	plan_id: string;
	plan_name: string;
	plan_display_name: string;
	plan_type: 'free' | 'starter' | 'pro' | 'business' | 'enterprise';
	status: 'active' | 'canceled' | 'past_due' | 'trialing' | 'paused' | 'expired';
	billing_interval: 'monthly' | 'yearly';
	price: number;
	currency: string;
	start_date: string;
	current_period_start: string | null;
	current_period_end: string | null;
	trial_end_date: string | null;
	canceled_at: string | null;
	cancel_reason: string | null;
}

export interface UserInvoice {
	id: string;
	invoice_number: string;
	status: 'draft' | 'pending' | 'paid' | 'void' | 'uncollectible';
	total: number;
	amount_paid: number;
	currency: string;
	invoice_date: string;
	paid_at: string | null;
	stripe_hosted_invoice_url: string | null;
	stripe_invoice_pdf: string | null;
}

export interface BillingInfo {
	subscription: UserSubscription | null;
	invoices: UserInvoice[];
}
