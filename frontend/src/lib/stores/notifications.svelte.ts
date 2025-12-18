import { notificationsApi } from '$lib/api';
import type {
	Notification,
	NotificationPreference,
	NotificationPreferenceUpdate,
	NotificationListParams
} from '$lib/api';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

class NotificationStore {
	// State
	notifications = $state<Notification[]>([]);
	unreadCount = $state(0);
	loading = $state(false);
	loadingPreferences = $state(false);
	preferences = $state<NotificationPreference | null>(null);
	error = $state<string | null>(null);

	// Pagination state
	currentPage = $state(1);
	totalPages = $state(0);
	total = $state(0);
	perPage = $state(20);

	// SSE state
	private eventSource: EventSource | null = null;
	private isConnected = $state(false);
	private reconnectAttempts = 0;
	private maxReconnectAttempts = 5;
	private reconnectDelay = 1000; // Start with 1 second

	// Derived
	hasUnread = $derived(this.unreadCount > 0);

	/**
	 * Fetch notifications with pagination
	 */
	async fetchNotifications(params: NotificationListParams = {}) {
		this.loading = true;
		this.error = null;

		try {
			const response = await notificationsApi.getNotifications({
				page: params.page ?? this.currentPage,
				per_page: params.per_page ?? this.perPage,
				unread_only: params.unread_only
			});

			this.notifications = response.items;
			this.currentPage = response.page;
			this.totalPages = response.pages;
			this.total = response.total;
			this.perPage = response.per_page;
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to fetch notifications';
			console.error('Failed to fetch notifications:', err);
		} finally {
			this.loading = false;
		}
	}

	/**
	 * Fetch unread count for badge display
	 */
	async fetchUnreadCount() {
		try {
			const response = await notificationsApi.getUnreadCount();
			this.unreadCount = response.count;
		} catch (err) {
			console.error('Failed to fetch unread count:', err);
		}
	}

	/**
	 * Mark a single notification as read
	 */
	async markAsRead(notificationId: string) {
		try {
			await notificationsApi.markAsRead(notificationId);

			// Update local state
			const notification = this.notifications.find((n) => n.id === notificationId);
			if (notification && !notification.read_at) {
				notification.read_at = new Date().toISOString();
				this.unreadCount = Math.max(0, this.unreadCount - 1);
			}

			return true;
		} catch (err) {
			console.error('Failed to mark notification as read:', err);
			return false;
		}
	}

	/**
	 * Mark all notifications as read
	 */
	async markAllAsRead() {
		try {
			const response = await notificationsApi.markAllAsRead();

			// Update local state
			const now = new Date().toISOString();
			this.notifications = this.notifications.map((n) => ({
				...n,
				read_at: n.read_at ?? now
			}));
			this.unreadCount = 0;

			return response.count;
		} catch (err) {
			console.error('Failed to mark all notifications as read:', err);
			return 0;
		}
	}

	/**
	 * Delete a notification
	 */
	async deleteNotification(notificationId: string) {
		try {
			await notificationsApi.deleteNotification(notificationId);

			// Update local state
			const notification = this.notifications.find((n) => n.id === notificationId);
			if (notification && !notification.read_at) {
				this.unreadCount = Math.max(0, this.unreadCount - 1);
			}

			this.notifications = this.notifications.filter((n) => n.id !== notificationId);
			this.total = Math.max(0, this.total - 1);

			return true;
		} catch (err) {
			console.error('Failed to delete notification:', err);
			return false;
		}
	}

	/**
	 * Fetch notification preferences
	 */
	async fetchPreferences() {
		this.loadingPreferences = true;

		try {
			this.preferences = await notificationsApi.getPreferences();
		} catch (err) {
			console.error('Failed to fetch notification preferences:', err);
		} finally {
			this.loadingPreferences = false;
		}
	}

	/**
	 * Update notification preferences
	 */
	async updatePreferences(data: NotificationPreferenceUpdate) {
		this.loadingPreferences = true;

		try {
			this.preferences = await notificationsApi.updatePreferences(data);
			return true;
		} catch (err) {
			console.error('Failed to update notification preferences:', err);
			return false;
		} finally {
			this.loadingPreferences = false;
		}
	}

	/**
	 * Connect to SSE stream for real-time notifications
	 */
	connect() {
		if (this.isConnected || typeof window === 'undefined') return;

		const token = localStorage.getItem('access_token');
		if (!token) {
			console.warn('No access token, cannot connect to notification stream');
			return;
		}

		// EventSource doesn't support custom headers, use query param or cookie
		// We'll use a workaround with fetch + ReadableStream for auth
		this.connectWithAuth(token);
	}

	private async connectWithAuth(token: string) {
		try {
			const response = await fetch(`${API_BASE}/notifications/stream`, {
				headers: {
					Authorization: `Bearer ${token}`,
					Accept: 'text/event-stream'
				}
			});

			if (!response.ok) {
				throw new Error(`SSE connection failed: ${response.status}`);
			}

			const reader = response.body?.getReader();
			if (!reader) {
				throw new Error('No response body');
			}

			this.isConnected = true;
			this.reconnectAttempts = 0;
			this.reconnectDelay = 1000;

			const decoder = new TextDecoder();
			let buffer = '';

			const processStream = async () => {
				try {
					while (this.isConnected) {
						const { done, value } = await reader.read();

						if (done) {
							break;
						}

						buffer += decoder.decode(value, { stream: true });

						// Process complete events
						const lines = buffer.split('\n');
						buffer = lines.pop() || '';

						let currentEvent = '';
						let currentData = '';

						for (const line of lines) {
							if (line.startsWith('event: ')) {
								currentEvent = line.slice(7);
							} else if (line.startsWith('data: ')) {
								currentData = line.slice(6);
							} else if (line === '' && currentEvent && currentData) {
								this.handleSSEEvent(currentEvent, currentData);
								currentEvent = '';
								currentData = '';
							}
						}
					}
				} catch (err) {
					console.error('SSE stream error:', err);
				} finally {
					reader.releaseLock();
					this.handleDisconnect();
				}
			};

			processStream();
		} catch (err) {
			console.error('SSE connection error:', err);
			this.handleDisconnect();
		}
	}

	private handleSSEEvent(event: string, data: string) {
		try {
			const parsed = JSON.parse(data);

			switch (event) {
				case 'connected':
					console.log('Notification SSE connected');
					this.unreadCount = parsed.count;
					break;

				case 'unread_count':
					this.unreadCount = parsed.count;
					break;

				case 'new_notification':
					// Add to top of notifications list if we have them loaded
					if (this.notifications.length > 0) {
						this.notifications = [parsed as Notification, ...this.notifications];
					}
					this.unreadCount++;
					break;

				case 'heartbeat':
					// Keep-alive, no action needed
					break;

				default:
					console.log('Unknown SSE event:', event, parsed);
			}
		} catch (err) {
			console.error('Failed to parse SSE event:', err);
		}
	}

	private handleDisconnect() {
		this.isConnected = false;

		// Attempt reconnect with exponential backoff
		if (this.reconnectAttempts < this.maxReconnectAttempts) {
			this.reconnectAttempts++;
			const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
			console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

			setTimeout(() => {
				if (!this.isConnected) {
					this.connect();
				}
			}, delay);
		} else {
			console.error('Max reconnect attempts reached, falling back to polling');
			// Fallback to polling if SSE fails
			this.startPollingFallback();
		}
	}

	private pollingInterval: ReturnType<typeof setInterval> | null = null;

	private startPollingFallback() {
		if (this.pollingInterval) return;

		this.fetchUnreadCount();
		this.pollingInterval = setInterval(() => {
			this.fetchUnreadCount();
		}, 60000);
	}

	/**
	 * Disconnect from SSE stream
	 */
	disconnect() {
		this.isConnected = false;

		if (this.pollingInterval) {
			clearInterval(this.pollingInterval);
			this.pollingInterval = null;
		}
	}

	// Backwards compatibility aliases
	startPolling() {
		this.connect();
	}

	stopPolling() {
		this.disconnect();
	}

	/**
	 * Reset store state (call on logout)
	 */
	reset() {
		this.stopPolling();
		this.notifications = [];
		this.unreadCount = 0;
		this.loading = false;
		this.loadingPreferences = false;
		this.preferences = null;
		this.error = null;
		this.currentPage = 1;
		this.totalPages = 0;
		this.total = 0;
	}

	/**
	 * Load next page of notifications
	 */
	async loadNextPage() {
		if (this.currentPage >= this.totalPages) return;

		await this.fetchNotifications({ page: this.currentPage + 1 });
	}

	/**
	 * Load previous page of notifications
	 */
	async loadPreviousPage() {
		if (this.currentPage <= 1) return;

		await this.fetchNotifications({ page: this.currentPage - 1 });
	}

	/**
	 * Refresh notifications (reload current page)
	 */
	async refresh() {
		await Promise.all([this.fetchNotifications(), this.fetchUnreadCount()]);
	}
}

export const notificationStore = new NotificationStore();
