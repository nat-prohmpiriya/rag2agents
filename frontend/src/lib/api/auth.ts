import { fetchApi, setStoredToken, setRefreshToken, removeStoredToken, getRefreshToken } from './client';
import type { TokenResponse, User, LoginRequest, RegisterRequest, MessageResponse } from '$lib/types';

export const authApi = {
	/**
	 * Login with email and password
	 */
	login: async (data: LoginRequest): Promise<TokenResponse> => {
		const response = await fetchApi<TokenResponse>('/auth/login', {
			method: 'POST',
			body: JSON.stringify(data),
		});

		// Store tokens
		setStoredToken(response.access_token);
		setRefreshToken(response.refresh_token);

		return response;
	},

	/**
	 * Register new user
	 */
	register: async (data: RegisterRequest): Promise<User> => {
		const response = await fetchApi<User>('/auth/register', {
			method: 'POST',
			body: JSON.stringify(data),
		});

		return response;
	},

	/**
	 * Logout - clear tokens
	 */
	logout: async (): Promise<void> => {
		try {
			await fetchApi<MessageResponse>('/auth/logout', { method: 'POST' });
		} catch {
			// Ignore errors, still clear local tokens
		}
		removeStoredToken();
	},

	/**
	 * Get current user info
	 */
	me: (): Promise<User> => {
		return fetchApi<User>('/auth/me');
	},

	/**
	 * Refresh access token
	 */
	refresh: async (): Promise<TokenResponse> => {
		const refreshToken = getRefreshToken();
		if (!refreshToken) {
			throw new Error('No refresh token available');
		}

		const response = await fetchApi<TokenResponse>('/auth/refresh', {
			method: 'POST',
			body: JSON.stringify({ refresh_token: refreshToken }),
		});

		setStoredToken(response.access_token);
		setRefreshToken(response.refresh_token);

		return response;
	},
};
