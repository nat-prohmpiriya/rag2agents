import { fetchApi } from './client';
import { ApiException } from '$lib/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ModelInfo {
	id: string;
	name: string;
	provider: string;
	description?: string;
	context_window?: number;
	input_price?: number;
	output_price?: number;
	tier?: 'free' | 'pro' | 'enterprise';
	model_page_url?: string;
	pricing_url?: string;
	terms_url?: string;
	privacy_url?: string;
	website_url?: string;
}

export interface ModelsResponse {
	models: ModelInfo[];
}

export interface ChatRequest {
	message: string;
	conversation_id?: string;
	model?: string;
	temperature?: number;
	max_tokens?: number;
	top_p?: number;
	frequency_penalty?: number;
	presence_penalty?: number;
	stream?: boolean;
}

export interface ChatMessage {
	role: string;
	content: string;
	created_at: string;
}

export interface UsageInfo {
	prompt_tokens: number;
	completion_tokens: number;
	total_tokens: number;
}

export interface ChatResponse {
	message: ChatMessage;
	model: string;
	usage: UsageInfo | null;
	conversation_id: string | null;
}

export interface StreamChunk {
	content: string;
	done: boolean;
	error?: string;
	conversation_id?: string;
}

export const chatApi = {
	/**
	 * Get available models
	 */
	getModels: async (): Promise<ModelsResponse> => {
		return fetchApi<ModelsResponse>('/api/chat/models', {
			method: 'GET',
		});
	},

	/**
	 * Send chat message (non-streaming)
	 */
	send: async (data: ChatRequest): Promise<ChatResponse> => {
		return fetchApi<ChatResponse>('/api/chat', {
			method: 'POST',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Send chat message with streaming response
	 */
	stream: async (
		data: ChatRequest,
		onChunk: (content: string) => void,
		onDone: (conversationId?: string) => void,
		onError: (error: string) => void
	): Promise<{ traceId: string | null; conversationId: string | null }> => {
		const token = localStorage.getItem('access_token');

		const response = await fetch(`${API_BASE}/api/chat/stream`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				...(token && { Authorization: `Bearer ${token}` }),
			},
			body: JSON.stringify({ ...data, stream: true }),
		});

		if (!response.ok) {
			let message = 'Chat failed';
			try {
				const errorData = await response.json();
				message = errorData.error || errorData.detail || message;
			} catch {
				message = await response.text();
			}
			throw new ApiException(response.status, message);
		}

		const traceId = response.headers.get('X-Trace-Id');
		const reader = response.body?.getReader();
		const decoder = new TextDecoder();

		if (!reader) {
			throw new Error('Response body is not readable');
		}

		let buffer = '';
		let conversationId: string | null = null;

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, { stream: true });

			// Parse SSE events
			const lines = buffer.split('\n\n');
			buffer = lines.pop() || ''; // Keep incomplete line in buffer

			for (const line of lines) {
				if (line.startsWith('data: ')) {
					try {
						const data = JSON.parse(line.slice(6)) as StreamChunk;
						// Capture conversation_id from first chunk
						if (data.conversation_id && !conversationId) {
							conversationId = data.conversation_id;
						}
						if (data.error) {
							onError(data.error);
							return { traceId, conversationId };
						}
						if (data.done) {
							onDone(conversationId || undefined);
							return { traceId, conversationId };
						}
						if (data.content) {
							onChunk(data.content);
						}
					} catch (e) {
						console.error('Failed to parse SSE data:', e);
					}
				}
			}
		}

		onDone(conversationId || undefined);
		return { traceId, conversationId };
	},
};
