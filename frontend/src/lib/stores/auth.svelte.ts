import { authApi } from '$lib/api';
import type { User, LoginRequest, RegisterRequest } from '$lib/types';

class AuthStore {
	user = $state<User | null>(null);
	isLoading = $state(true);

	isAuthenticated = $derived(this.user !== null);

	async initialize() {
		if (typeof window === 'undefined') {
			this.isLoading = false;
			return;
		}

		const token = localStorage.getItem('access_token');
		if (!token) {
			this.isLoading = false;
			return;
		}

		try {
			this.user = await authApi.me();
		} catch {
			localStorage.removeItem('access_token');
			localStorage.removeItem('refresh_token');
			this.user = null;
		} finally {
			this.isLoading = false;
		}
	}

	async login(input: LoginRequest) {
		await authApi.login(input);
		this.user = await authApi.me();
	}

	async register(input: RegisterRequest) {
		await authApi.register(input);
		await authApi.login({ email: input.email, password: input.password });
		this.user = await authApi.me();
	}

	async logout() {
		await authApi.logout();
		this.user = null;
	}
}

export const auth = new AuthStore();
