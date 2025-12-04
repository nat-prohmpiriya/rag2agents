/**
 * Admin API client
 */

import { fetchApi } from './client';

// Types
export interface UserStats {
	total_users: number;
	active_today: number;
	new_this_week: number;
	new_this_month: number;
}

export interface UsageStats {
	requests_today: number;
	requests_this_month: number;
	tokens_today: number;
	tokens_this_month: number;
	cost_today: number;
	cost_this_month: number;
}

export interface RevenueStats {
	mrr: number;
	arr: number;
	total_revenue: number;
	revenue_this_month: number;
}

export interface PlanSubscriberCount {
	plan_id: string;
	plan_name: string;
	display_name: string;
	subscriber_count: number;
	percentage: number;
}

export interface DailyUsage {
	date: string;
	requests: number;
	tokens: number;
	cost: number;
}

export interface DashboardStats {
	users: UserStats;
	usage: UsageStats;
	revenue: RevenueStats;
	subscribers_by_plan: PlanSubscriberCount[];
	usage_over_time: DailyUsage[];
}

export interface Plan {
	id: string;
	name: string;
	display_name: string;
	description: string | null;
	plan_type: 'free' | 'pro' | 'enterprise';
	price_monthly: number;
	price_yearly: number | null;
	currency: string;
	tokens_per_month: number;
	requests_per_minute: number;
	requests_per_day: number;
	max_documents: number;
	max_projects: number;
	max_agents: number;
	allowed_models: string[];
	features: Record<string, unknown> | null;
	is_active: boolean;
	is_public: boolean;
	stripe_price_id_monthly: string | null;
	stripe_price_id_yearly: string | null;
	stripe_product_id: string | null;
	created_at: string;
	updated_at: string;
	subscriber_count?: number;
}

export interface PlanListResponse {
	items: Plan[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface Subscription {
	id: string;
	user_id: string;
	plan_id: string;
	status: 'active' | 'canceled' | 'past_due' | 'trialing' | 'paused' | 'expired';
	billing_interval: 'monthly' | 'yearly';
	start_date: string;
	end_date: string | null;
	trial_end_date: string | null;
	canceled_at: string | null;
	current_period_start: string | null;
	current_period_end: string | null;
	stripe_subscription_id: string | null;
	stripe_customer_id: string | null;
	litellm_key_id: string | null;
	litellm_team_id: string | null;
	cancel_reason: string | null;
	created_at: string;
	updated_at: string;
	user: {
		id: string;
		email: string;
		username: string;
	};
	plan: {
		id: string;
		name: string;
		display_name: string;
		price_monthly: number;
		price_yearly: number | null;
	};
}

export interface SubscriptionListResponse {
	items: Subscription[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

// API Functions

export async function getDashboardStats(): Promise<DashboardStats> {
	return fetchApi<DashboardStats>('/api/admin/dashboard');
}

export async function getPlans(
	page = 1,
	perPage = 20,
	includeInactive = true
): Promise<PlanListResponse> {
	const params = new URLSearchParams({
		page: String(page),
		per_page: String(perPage),
		include_inactive: String(includeInactive)
	});
	return fetchApi<PlanListResponse>(`/api/admin/plans?${params}`);
}

export async function getPlan(id: string): Promise<Plan> {
	return fetchApi<Plan>(`/api/admin/plans/${id}`);
}

export async function createPlan(data: Partial<Plan>): Promise<Plan> {
	return fetchApi<Plan>('/api/admin/plans', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updatePlan(id: string, data: Partial<Plan>): Promise<Plan> {
	return fetchApi<Plan>(`/api/admin/plans/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function deletePlan(id: string): Promise<void> {
	await fetchApi<{ message: string }>(`/api/admin/plans/${id}`, {
		method: 'DELETE'
	});
}

export async function getSubscriptions(
	page = 1,
	perPage = 20,
	filters?: { status?: string; plan_id?: string; user_id?: string }
): Promise<SubscriptionListResponse> {
	const params = new URLSearchParams({
		page: String(page),
		per_page: String(perPage)
	});

	if (filters?.status) params.set('status', filters.status);
	if (filters?.plan_id) params.set('plan_id', filters.plan_id);
	if (filters?.user_id) params.set('user_id', filters.user_id);

	return fetchApi<SubscriptionListResponse>(`/api/admin/subscriptions?${params}`);
}

export async function getSubscription(id: string): Promise<Subscription> {
	return fetchApi<Subscription>(`/api/admin/subscriptions/${id}`);
}

export async function upgradeSubscription(
	id: string,
	newPlanId: string,
	billingInterval?: 'monthly' | 'yearly'
): Promise<Subscription> {
	return fetchApi<Subscription>(`/api/admin/subscriptions/${id}/upgrade`, {
		method: 'POST',
		body: JSON.stringify({
			new_plan_id: newPlanId,
			billing_interval: billingInterval
		})
	});
}

export async function downgradeSubscription(
	id: string,
	newPlanId: string,
	effectiveAtPeriodEnd = true
): Promise<Subscription> {
	return fetchApi<Subscription>(`/api/admin/subscriptions/${id}/downgrade`, {
		method: 'POST',
		body: JSON.stringify({
			new_plan_id: newPlanId,
			effective_at_period_end: effectiveAtPeriodEnd
		})
	});
}

export async function cancelSubscription(
	id: string,
	cancelReason?: string,
	cancelAtPeriodEnd = true
): Promise<Subscription> {
	return fetchApi<Subscription>(`/api/admin/subscriptions/${id}/cancel`, {
		method: 'POST',
		body: JSON.stringify({
			cancel_reason: cancelReason,
			cancel_at_period_end: cancelAtPeriodEnd
		})
	});
}

// User Management Types
export interface AdminUser {
	id: string;
	email: string;
	username: string;
	first_name: string | null;
	last_name: string | null;
	is_active: boolean;
	is_superuser: boolean;
	tier: string;
	status: string;
	plan_name: string | null;
	subscription_status: string | null;
	tokens_used: number;
	tokens_limit: number;
	revenue_total: number;
	last_active: string | null;
	created_at: string;
	updated_at: string;
}

export interface AdminUserListResponse {
	items: AdminUser[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface UserActionResult {
	success: boolean;
	user_id: string;
	message: string;
}

export interface BulkActionResponse {
	results: UserActionResult[];
	success_count: number;
	failure_count: number;
}

// User Management API Functions

export async function getUsers(
	page = 1,
	perPage = 20,
	filters?: { search?: string; plan?: string; status?: string }
): Promise<AdminUserListResponse> {
	const params = new URLSearchParams({
		page: String(page),
		per_page: String(perPage)
	});

	if (filters?.search) params.set('search', filters.search);
	if (filters?.plan) params.set('plan', filters.plan);
	if (filters?.status) params.set('status', filters.status);

	return fetchApi<AdminUserListResponse>(`/api/admin/users?${params}`);
}

export async function getUser(id: string): Promise<AdminUser> {
	return fetchApi<AdminUser>(`/api/admin/users/${id}`);
}

export async function updateUser(
	id: string,
	data: {
		first_name?: string;
		last_name?: string;
		is_active?: boolean;
		is_superuser?: boolean;
		tier?: string;
	}
): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/api/admin/users/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function changeUserPlan(id: string, planId: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/api/admin/users/${id}/change-plan`, {
		method: 'POST',
		body: JSON.stringify({ plan_id: planId })
	});
}

export async function suspendUser(id: string, reason?: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/api/admin/users/${id}/suspend`, {
		method: 'POST',
		body: JSON.stringify({ reason })
	});
}

export async function activateUser(id: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/api/admin/users/${id}/activate`, {
		method: 'POST'
	});
}

export async function banUser(id: string, reason?: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/api/admin/users/${id}/ban`, {
		method: 'POST',
		body: JSON.stringify({ reason })
	});
}

export async function deleteUser(id: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/api/admin/users/${id}`, {
		method: 'DELETE'
	});
}

export async function bulkUserAction(
	userIds: string[],
	action: 'change_plan' | 'suspend' | 'activate',
	planId?: string
): Promise<BulkActionResponse> {
	return fetchApi<BulkActionResponse>('/api/admin/users/bulk-action', {
		method: 'POST',
		body: JSON.stringify({
			user_ids: userIds,
			action,
			plan_id: planId
		})
	});
}
