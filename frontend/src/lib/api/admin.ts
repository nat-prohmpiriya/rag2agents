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
	return fetchApi<DashboardStats>('/admin/dashboard');
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
	return fetchApi<PlanListResponse>(`/admin/plans?${params}`);
}

export async function getPlan(id: string): Promise<Plan> {
	return fetchApi<Plan>(`/admin/plans/${id}`);
}

export async function createPlan(data: Partial<Plan>): Promise<Plan> {
	return fetchApi<Plan>('/admin/plans', {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export async function updatePlan(id: string, data: Partial<Plan>): Promise<Plan> {
	return fetchApi<Plan>(`/admin/plans/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function deletePlan(id: string): Promise<void> {
	await fetchApi<{ message: string }>(`/admin/plans/${id}`, {
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

	return fetchApi<SubscriptionListResponse>(`/admin/subscriptions?${params}`);
}

export async function getSubscription(id: string): Promise<Subscription> {
	return fetchApi<Subscription>(`/admin/subscriptions/${id}`);
}

export async function upgradeSubscription(
	id: string,
	newPlanId: string,
	billingInterval?: 'monthly' | 'yearly'
): Promise<Subscription> {
	return fetchApi<Subscription>(`/admin/subscriptions/${id}/upgrade`, {
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
	return fetchApi<Subscription>(`/admin/subscriptions/${id}/downgrade`, {
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
	return fetchApi<Subscription>(`/admin/subscriptions/${id}/cancel`, {
		method: 'POST',
		body: JSON.stringify({
			cancel_reason: cancelReason,
			cancel_at_period_end: cancelAtPeriodEnd
		})
	});
}

export async function reactivateSubscription(id: string): Promise<Subscription> {
	return fetchApi<Subscription>(`/admin/subscriptions/${id}/reactivate`, {
		method: 'POST'
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

	return fetchApi<AdminUserListResponse>(`/admin/users?${params}`);
}

export async function getUser(id: string): Promise<AdminUser> {
	return fetchApi<AdminUser>(`/admin/users/${id}`);
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
	return fetchApi<{ message: string }>(`/admin/users/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function changeUserPlan(id: string, planId: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/admin/users/${id}/change-plan`, {
		method: 'POST',
		body: JSON.stringify({ plan_id: planId })
	});
}

export async function suspendUser(id: string, reason?: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/admin/users/${id}/suspend`, {
		method: 'POST',
		body: JSON.stringify({ reason })
	});
}

export async function activateUser(id: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/admin/users/${id}/activate`, {
		method: 'POST'
	});
}

export async function banUser(id: string, reason?: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/admin/users/${id}/ban`, {
		method: 'POST',
		body: JSON.stringify({ reason })
	});
}

export async function deleteUser(id: string): Promise<{ message: string }> {
	return fetchApi<{ message: string }>(`/admin/users/${id}`, {
		method: 'DELETE'
	});
}

export async function bulkUserAction(
	userIds: string[],
	action: 'change_plan' | 'suspend' | 'activate',
	planId?: string
): Promise<BulkActionResponse> {
	return fetchApi<BulkActionResponse>('/admin/users/bulk-action', {
		method: 'POST',
		body: JSON.stringify({
			user_ids: userIds,
			action,
			plan_id: planId
		})
	});
}

// User Detail Types
export interface UserSubscriptionDetail {
	id: string;
	plan_name: string;
	plan_display_name: string;
	status: string;
	billing_interval: string;
	price: number;
	start_date: string;
	current_period_start: string | null;
	current_period_end: string | null;
	trial_end_date: string | null;
	canceled_at: string | null;
	cancel_reason: string | null;
}

export interface UserUsageDetail {
	tokens_used_today: number;
	tokens_used_this_month: number;
	tokens_limit: number;
	requests_today: number;
	requests_this_month: number;
	cost_today: number;
	cost_this_month: number;
}

export interface UserUsageHistory {
	date: string;
	tokens: number;
	requests: number;
	cost: number;
}

export interface UserConversationSummary {
	id: string;
	title: string | null;
	message_count: number;
	last_message_at: string | null;
	created_at: string;
}

export interface UserDocumentSummary {
	id: string;
	filename: string;
	file_type: string;
	file_size: number;
	status: string;
	chunk_count: number;
	created_at: string;
}

export interface UserInvoiceSummary {
	id: string;
	invoice_number: string;
	status: string;
	total: number;
	amount_paid: number;
	currency: string;
	invoice_date: string;
	paid_at: string | null;
}

export interface UserDetail {
	id: string;
	email: string;
	username: string;
	first_name: string | null;
	last_name: string | null;
	is_active: boolean;
	is_superuser: boolean;
	tier: string;
	created_at: string;
	updated_at: string;
	active_subscription: UserSubscriptionDetail | null;
	subscription_history: UserSubscriptionDetail[];
	usage: UserUsageDetail;
	usage_history: UserUsageHistory[];
	total_conversations: number;
	total_documents: number;
	total_projects: number;
	total_revenue: number;
	invoices: UserInvoiceSummary[];
	recent_conversations: UserConversationSummary[];
	recent_documents: UserDocumentSummary[];
}

export async function getUserDetail(id: string): Promise<UserDetail> {
	return fetchApi<UserDetail>(`/admin/users/${id}/detail`);
}

// Usage Analytics Types
export interface UsageSummary {
	total_requests: number;
	total_tokens: number;
	total_cost: number;
	requests_today: number;
	tokens_today: number;
	cost_today: number;
	period_days: number;
}

export interface ModelUsage {
	model: string;
	requests: number;
	prompt_tokens: number;
	completion_tokens: number;
	total_tokens: number;
	cost: number;
}

export interface DailyUsageData {
	date: string;
	requests: number;
	tokens: number;
	cost: number;
}

export interface PlanUsage {
	plan_id: string;
	plan_name: string;
	users_count: number;
	total_requests: number;
	total_tokens: number;
	total_cost: number;
	revenue: number;
	profit_margin: number;
}

export interface UserSpendData {
	user_id: string | null;
	user_email: string | null;
	total_spend: number;
	total_requests?: number;
	total_tokens?: number;
	[key: string]: unknown;
}

export interface UsageAnalytics {
	summary: UsageSummary;
	by_user: UserSpendData[];
	by_model: ModelUsage[];
	by_date: DailyUsageData[];
	by_plan: PlanUsage[];
}

export async function getUsageAnalytics(days: number = 30): Promise<UsageAnalytics> {
	return fetchApi<UsageAnalytics>(`/admin/usage?days=${days}`);
}

// System Health Types
export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export interface LiteLLMHealth {
	status: ServiceStatus;
	url: string;
	response_time_ms: number | null;
	models_available: number;
	error: string | null;
}

export interface PostgreSQLHealth {
	status: ServiceStatus;
	host: string;
	active_connections: number;
	max_connections: number;
	database_size_mb: number;
	response_time_ms: number | null;
	error: string | null;
}

export interface RedisHealth {
	status: ServiceStatus;
	host: string;
	port: number;
	used_memory_mb: number;
	max_memory_mb: number;
	connected_clients: number;
	hit_rate: number;
	response_time_ms: number | null;
	error: string | null;
}

export interface SystemHealth {
	overall_status: ServiceStatus;
	timestamp: string;
	litellm: LiteLLMHealth;
	postgresql: PostgreSQLHealth;
	redis: RedisHealth;
}

export interface SystemMetrics {
	requests_per_second: number;
	avg_response_time_ms: number;
	error_rate_percent: number;
	active_users: number;
	uptime_seconds: number;
}

// System Health API Functions
export async function getSystemHealth(): Promise<SystemHealth> {
	return fetchApi<SystemHealth>('/admin/system/health');
}

export async function getSystemMetrics(): Promise<SystemMetrics> {
	return fetchApi<SystemMetrics>('/admin/system/metrics');
}

// Audit Log Types
export interface AuditLogAdmin {
	id: string;
	email: string;
	username: string;
}

export interface AuditLog {
	id: string;
	admin_id: string | null;
	admin: AuditLogAdmin | null;
	action: string;
	description: string;
	target_type: string | null;
	target_id: string | null;
	details: Record<string, unknown> | null;
	ip_address: string | null;
	user_agent: string | null;
	created_at: string;
}

export interface AuditLogListResponse {
	items: AuditLog[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface AuditActionType {
	value: string;
	label: string;
}

export interface AuditLogFilters {
	action?: string;
	admin_id?: string;
	target_type?: string;
	target_id?: string;
	start_date?: string;
	end_date?: string;
	search?: string;
}

// Audit Log API Functions
export async function getAuditLogs(
	page = 1,
	perPage = 20,
	filters?: AuditLogFilters
): Promise<AuditLogListResponse> {
	const params = new URLSearchParams({
		page: String(page),
		per_page: String(perPage)
	});

	if (filters?.action) params.set('action', filters.action);
	if (filters?.admin_id) params.set('admin_id', filters.admin_id);
	if (filters?.target_type) params.set('target_type', filters.target_type);
	if (filters?.target_id) params.set('target_id', filters.target_id);
	if (filters?.start_date) params.set('start_date', filters.start_date);
	if (filters?.end_date) params.set('end_date', filters.end_date);
	if (filters?.search) params.set('search', filters.search);

	return fetchApi<AuditLogListResponse>(`/admin/audit?${params}`);
}

export async function getAuditLog(id: string): Promise<AuditLog> {
	return fetchApi<AuditLog>(`/admin/audit/${id}`);
}

export async function getAuditActionTypes(): Promise<AuditActionType[]> {
	return fetchApi<AuditActionType[]>('/admin/audit/actions');
}

export async function getAuditTargetTypes(): Promise<string[]> {
	return fetchApi<string[]>('/admin/audit/target-types');
}

export async function getAuditAdmins(): Promise<AuditLogAdmin[]> {
	return fetchApi<AuditLogAdmin[]>('/admin/audit/admins');
}

// Settings Types
export interface GeneralSettings {
	site_name: string;
	default_plan_id: string | null;
	trial_period_days: number;
	allow_registration: boolean;
	require_email_verification: boolean;
}

export interface PaymentSettings {
	stripe_publishable_key: string | null;
	stripe_secret_key: string | null;
	stripe_webhook_secret: string | null;
	currency: string;
	tax_rate_percent: number;
}

export interface LiteLLMSettings {
	proxy_url: string | null;
	master_key: string | null;
	default_model: string;
	fallback_model: string | null;
	request_timeout_seconds: number;
}

export interface NotificationSettings {
	slack_webhook_url: string | null;
	email_enabled: boolean;
	email_from_name: string;
	email_from_address: string | null;
	smtp_host: string | null;
	smtp_port: number;
	smtp_username: string | null;
	smtp_password: string | null;
	smtp_use_tls: boolean;
}

export interface AllSettings {
	general: GeneralSettings;
	payment: PaymentSettings;
	litellm: LiteLLMSettings;
	notification: NotificationSettings;
}

export interface AllSettingsUpdate {
	general?: GeneralSettings;
	payment?: PaymentSettings;
	litellm?: LiteLLMSettings;
	notification?: NotificationSettings;
}

export interface SettingRaw {
	id: string;
	key: string;
	value: string | null;
	value_json: Record<string, unknown> | null;
	category: string;
	description: string | null;
	is_secret: boolean;
	is_editable: boolean;
	created_at: string;
	updated_at: string;
}

// Settings API Functions
export async function getAllSettings(): Promise<AllSettings> {
	return fetchApi<AllSettings>('/admin/settings');
}

export async function updateAllSettings(data: AllSettingsUpdate): Promise<AllSettings> {
	return fetchApi<AllSettings>('/admin/settings', {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function getGeneralSettings(): Promise<GeneralSettings> {
	return fetchApi<GeneralSettings>('/admin/settings/general');
}

export async function updateGeneralSettings(data: GeneralSettings): Promise<GeneralSettings> {
	return fetchApi<GeneralSettings>('/admin/settings/general', {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function getPaymentSettings(): Promise<PaymentSettings> {
	return fetchApi<PaymentSettings>('/admin/settings/payment');
}

export async function updatePaymentSettings(data: PaymentSettings): Promise<PaymentSettings> {
	return fetchApi<PaymentSettings>('/admin/settings/payment', {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function getLiteLLMSettings(): Promise<LiteLLMSettings> {
	return fetchApi<LiteLLMSettings>('/admin/settings/litellm');
}

export async function updateLiteLLMSettings(data: LiteLLMSettings): Promise<LiteLLMSettings> {
	return fetchApi<LiteLLMSettings>('/admin/settings/litellm', {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function getNotificationSettings(): Promise<NotificationSettings> {
	return fetchApi<NotificationSettings>('/admin/settings/notification');
}

export async function updateNotificationSettings(
	data: NotificationSettings
): Promise<NotificationSettings> {
	return fetchApi<NotificationSettings>('/admin/settings/notification', {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

export async function initializeSettings(): Promise<{ message: string }> {
	return fetchApi<{ message: string }>('/admin/settings/initialize', {
		method: 'POST'
	});
}

export async function getRawSettings(category?: string): Promise<SettingRaw[]> {
	const params = category ? `?category=${category}` : '';
	return fetchApi<SettingRaw[]>(`/admin/settings/raw${params}`);
}

export async function updateRawSetting(
	key: string,
	data: { value?: string; value_json?: Record<string, unknown>; description?: string }
): Promise<SettingRaw> {
	return fetchApi<SettingRaw>(`/admin/settings/raw/${key}`, {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}
