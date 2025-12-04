/**
 * Notification API client
 */

import { fetchApi } from './client';

// Types
export type NotificationType =
	| 'quota_warning'
	| 'quota_exceeded'
	| 'subscription_expiring'
	| 'subscription_renewed'
	| 'payment_failed'
	| 'payment_success'
	| 'document_processed'
	| 'document_failed'
	| 'system_maintenance'
	| 'system_announcement'
	| 'welcome'
	| 'password_changed';

export type NotificationCategory = 'billing' | 'document' | 'system' | 'account';

export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical';

export interface Notification {
	id: string;
	user_id: string;
	type: NotificationType;
	category: NotificationCategory;
	title: string;
	message: string;
	priority: NotificationPriority;
	read_at: string | null;
	action_url: string | null;
	extra_data: Record<string, unknown> | null;
	expires_at: string | null;
	created_at: string;
	updated_at: string;
}

export interface NotificationListResponse {
	items: Notification[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface UnreadCountResponse {
	count: number;
}

export interface MarkAsReadResponse {
	success: boolean;
	read_at: string;
}

export interface MarkAllAsReadResponse {
	success: boolean;
	count: number;
}

export interface CategorySetting {
	email: boolean;
	in_app: boolean;
}

export interface CategorySettings {
	billing: CategorySetting;
	document: CategorySetting;
	system: CategorySetting;
	account: CategorySetting;
}

export interface NotificationPreference {
	id: string;
	user_id: string;
	email_enabled: boolean;
	in_app_enabled: boolean;
	category_settings: CategorySettings;
	quiet_hours_start: string | null;
	quiet_hours_end: string | null;
	created_at: string;
	updated_at: string;
}

export interface NotificationPreferenceUpdate {
	email_enabled?: boolean;
	in_app_enabled?: boolean;
	category_settings?: CategorySettings;
	quiet_hours_start?: string | null;
	quiet_hours_end?: string | null;
}

export interface NotificationListParams {
	page?: number;
	per_page?: number;
	unread_only?: boolean;
}

// API Functions

/**
 * Get paginated list of notifications for the current user
 */
export async function getNotifications(
	params: NotificationListParams = {}
): Promise<NotificationListResponse> {
	const searchParams = new URLSearchParams();

	if (params.page) searchParams.set('page', String(params.page));
	if (params.per_page) searchParams.set('per_page', String(params.per_page));
	if (params.unread_only) searchParams.set('unread_only', 'true');

	const query = searchParams.toString();
	const url = query ? `/api/notifications?${query}` : '/api/notifications';

	return fetchApi<NotificationListResponse>(url);
}

/**
 * Get unread notification count for badge display
 */
export async function getUnreadCount(): Promise<UnreadCountResponse> {
	return fetchApi<UnreadCountResponse>('/api/notifications/unread-count');
}

/**
 * Mark a single notification as read
 */
export async function markAsRead(notificationId: string): Promise<MarkAsReadResponse> {
	return fetchApi<MarkAsReadResponse>(`/api/notifications/${notificationId}/read`, {
		method: 'POST'
	});
}

/**
 * Mark all notifications as read
 */
export async function markAllAsRead(): Promise<MarkAllAsReadResponse> {
	return fetchApi<MarkAllAsReadResponse>('/api/notifications/read-all', {
		method: 'POST'
	});
}

/**
 * Delete a notification (soft delete)
 */
export async function deleteNotification(
	notificationId: string
): Promise<{ success: boolean; message: string }> {
	return fetchApi<{ success: boolean; message: string }>(`/api/notifications/${notificationId}`, {
		method: 'DELETE'
	});
}

/**
 * Get notification preferences for the current user
 */
export async function getPreferences(): Promise<NotificationPreference> {
	return fetchApi<NotificationPreference>('/api/notifications/preferences');
}

/**
 * Update notification preferences for the current user
 */
export async function updatePreferences(
	data: NotificationPreferenceUpdate
): Promise<NotificationPreference> {
	return fetchApi<NotificationPreference>('/api/notifications/preferences', {
		method: 'PUT',
		body: JSON.stringify(data)
	});
}

// Convenience object for namespaced exports
export const notificationsApi = {
	getNotifications,
	getUnreadCount,
	markAsRead,
	markAllAsRead,
	deleteNotification,
	getPreferences,
	updatePreferences
};
