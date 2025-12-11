import { ApiException, type BaseResponse } from '$lib/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

function getStoredToken(): string | null {
	if (typeof window === 'undefined') return null;
	return localStorage.getItem('access_token');
}

export function setStoredToken(token: string): void {
	if (typeof window === 'undefined') return;
	localStorage.setItem('access_token', token);
}

export function removeStoredToken(): void {
	if (typeof window === 'undefined') return;
	localStorage.removeItem('access_token');
	localStorage.removeItem('refresh_token');
}

export function setRefreshToken(token: string): void {
	if (typeof window === 'undefined') return;
	localStorage.setItem('refresh_token', token);
}

export function getRefreshToken(): string | null {
	if (typeof window === 'undefined') return null;
	return localStorage.getItem('refresh_token');
}

/**
 * Fetch wrapper for API calls with authentication
 * Automatically unwraps BaseResponse<T> to return T
 */
export async function fetchApi<T>(
	endpoint: string,
	options?: RequestInit
): Promise<T> {
	const token = getStoredToken();

	const response = await fetch(`${API_BASE}${endpoint}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(token && { Authorization: `Bearer ${token}` }),
			...options?.headers,
		},
	});

	if (!response.ok) {
		let message = 'An error occurred';
		let traceId: string | undefined;
		let detail: string | undefined;

		try {
			const errorData = await response.json();
			// Backend returns { trace_id, error, detail } for errors
			message = errorData.error || errorData.detail || errorData.message || message;
			traceId = errorData.trace_id;
			detail = errorData.detail;
		} catch {
			message = await response.text();
		}

		throw new ApiException(response.status, message, traceId, detail);
	}

	// Handle 204 No Content
	if (response.status === 204) {
		return undefined as T;
	}

	const json = await response.json();

	// Backend wraps responses in BaseResponse<T> with { trace_id, data }
	// Unwrap and return just the data
	if ('data' in json && 'trace_id' in json) {
		return (json as BaseResponse<T>).data;
	}

	// Fallback for endpoints that don't use BaseResponse wrapper
	return json as T;
}

/**
 * Fetch wrapper that returns the full BaseResponse (including trace_id)
 */
export async function fetchApiWithTrace<T>(
	endpoint: string,
	options?: RequestInit
): Promise<BaseResponse<T>> {
	const token = getStoredToken();

	const response = await fetch(`${API_BASE}${endpoint}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(token && { Authorization: `Bearer ${token}` }),
			...options?.headers,
		},
	});

	if (!response.ok) {
		let message = 'An error occurred';
		let traceId: string | undefined;
		let detail: string | undefined;

		try {
			const errorData = await response.json();
			message = errorData.error || errorData.detail || errorData.message || message;
			traceId = errorData.trace_id;
			detail = errorData.detail;
		} catch {
			message = await response.text();
		}

		throw new ApiException(response.status, message, traceId, detail);
	}

	return response.json();
}

/**
 * Fetch wrapper for streaming responses (SSE/ReadableStream)
 * Returns trace_id from X-Trace-Id header
 */
export async function fetchStream(
	endpoint: string,
	options: RequestInit,
	onChunk: (chunk: string) => void
): Promise<{ traceId: string | null }> {
	const token = getStoredToken();

	const response = await fetch(`${API_BASE}${endpoint}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(token && { Authorization: `Bearer ${token}` }),
			...options?.headers,
		},
	});

	if (!response.ok) {
		let message = 'An error occurred';
		let traceId: string | undefined;
		try {
			const errorData = await response.json();
			message = errorData.error || errorData.detail || errorData.message || message;
			traceId = errorData.trace_id;
		} catch {
			message = await response.text();
		}
		throw new ApiException(response.status, message, traceId);
	}

	// Get trace_id from header (streaming responses use header instead of body)
	const traceId = response.headers.get('X-Trace-Id');

	const reader = response.body?.getReader();
	const decoder = new TextDecoder();

	if (!reader) {
		throw new Error('Response body is not readable');
	}

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;
		onChunk(decoder.decode(value, { stream: true }));
	}

	return { traceId };
}

/**
 * Upload file with progress tracking
 */
export async function uploadFile<T>(
	endpoint: string,
	file: File,
	onProgress?: (percent: number) => void
): Promise<T> {
	const token = getStoredToken();

	return new Promise((resolve, reject) => {
		const xhr = new XMLHttpRequest();

		xhr.upload.addEventListener('progress', (event) => {
			if (event.lengthComputable && onProgress) {
				const percent = Math.round((event.loaded / event.total) * 100);
				onProgress(percent);
			}
		});

		xhr.addEventListener('load', () => {
			if (xhr.status >= 200 && xhr.status < 300) {
				try {
					const json = JSON.parse(xhr.responseText);
					// Unwrap BaseResponse
					if ('data' in json && 'trace_id' in json) {
						resolve(json.data);
					} else {
						resolve(json);
					}
				} catch {
					resolve(xhr.responseText as T);
				}
			} else {
				let message = 'Upload failed';
				let traceId: string | undefined;
				try {
					const errorData = JSON.parse(xhr.responseText);
					message = errorData.error || errorData.detail || errorData.message || message;
					traceId = errorData.trace_id;
				} catch {
					message = xhr.responseText || message;
				}
				reject(new ApiException(xhr.status, message, traceId));
			}
		});

		xhr.addEventListener('error', () => {
			reject(new ApiException(0, 'Network error during upload'));
		});

		const formData = new FormData();
		formData.append('file', file);

		xhr.open('POST', `${API_BASE}${endpoint}`);
		if (token) {
			xhr.setRequestHeader('Authorization', `Bearer ${token}`);
		}
		xhr.send(formData);
	});
}
