import { fetchApi } from './client';

export interface UserProfile {
	id: string;
	email: string;
	username: string;
	first_name: string | null;
	last_name: string | null;
	is_active: boolean;
	tier: string;
	created_at: string;
	updated_at: string;
}

export interface UserStats {
	conversations_count: number;
	documents_count: number;
	agents_count: number;
	total_messages: number;
}

export interface UserUsage {
	total_tokens: number;
	total_messages: number;
	tokens_this_month: number;
	messages_this_month: number;
	estimated_cost: number;
	cost_this_month: number;
	quota?: {
		tokens_limit: number;
		tokens_used: number;
		percentage: number;
	};
}

export interface UserUpdate {
	username?: string;
	first_name?: string;
	last_name?: string;
}

export interface ChangePasswordRequest {
	current_password: string;
	new_password: string;
	confirm_password: string;
}

export interface DeleteAccountRequest {
	password: string;
	confirmation: string;
}

export interface MessageResponse {
	message: string;
}

export const profileApi = {
	/**
	 * Get current user's profile
	 */
	getProfile: async (): Promise<UserProfile> => {
		return fetchApi<UserProfile>('/profile');
	},

	/**
	 * Update current user's profile
	 */
	updateProfile: async (data: UserUpdate): Promise<UserProfile> => {
		return fetchApi<UserProfile>('/profile', {
			method: 'PUT',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Change current user's password
	 */
	changePassword: async (data: ChangePasswordRequest): Promise<MessageResponse> => {
		return fetchApi<MessageResponse>('/profile/change-password', {
			method: 'POST',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Delete current user's account (soft delete)
	 */
	deleteAccount: async (data: DeleteAccountRequest): Promise<MessageResponse> => {
		return fetchApi<MessageResponse>('/profile/delete-account', {
			method: 'POST',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Get current user's usage statistics
	 */
	getStats: async (): Promise<UserStats> => {
		return fetchApi<UserStats>('/profile/stats');
	},

	/**
	 * Get current user's usage data (tokens, cost, quota)
	 */
	getUsage: async (): Promise<UserUsage> => {
		return fetchApi<UserUsage>('/profile/usage');
	},
};
