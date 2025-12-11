import { fetchApi } from './client';

export interface Message {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	created_at: string;
	tokens_used: number | null;
}

export interface Conversation {
	id: string;
	title: string | null;
	created_at: string;
	updated_at: string;
	message_count: number;
	last_message_preview: string | null;
}

export interface ConversationDetail {
	id: string;
	title: string | null;
	messages: Message[];
	created_at: string;
	updated_at: string;
}

export interface PaginatedResponse<T> {
	items: T[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface CreateConversationRequest {
	title?: string;
	project_id?: string;
}

export interface UpdateConversationRequest {
	title: string;
}

export interface ConversationSearchResult {
	conversation_id: string;
	title: string | null;
	snippet: string; // Contains <mark> tags for highlighting
	match_count: number;
	rank: number;
	created_at: string;
}

export interface ConversationSearchResponse {
	items: ConversationSearchResult[];
	total: number;
	query: string;
}

export const conversationsApi = {
	/**
	 * List conversations for current user
	 */
	list: async (page: number = 1, perPage: number = 20): Promise<PaginatedResponse<Conversation>> => {
		return fetchApi<PaginatedResponse<Conversation>>(
			`/api/conversations?page=${page}&per_page=${perPage}`,
			{ method: 'GET' }
		);
	},

	/**
	 * Create a new conversation
	 */
	create: async (data?: CreateConversationRequest): Promise<Conversation> => {
		return fetchApi<Conversation>('/conversations', {
			method: 'POST',
			body: JSON.stringify(data || {}),
		});
	},

	/**
	 * Get conversation detail with messages
	 */
	get: async (id: string): Promise<ConversationDetail> => {
		return fetchApi<ConversationDetail>(`/api/conversations/${id}`, {
			method: 'GET',
		});
	},

	/**
	 * Update conversation title
	 */
	update: async (id: string, title: string): Promise<Conversation> => {
		return fetchApi<Conversation>(`/api/conversations/${id}`, {
			method: 'PATCH',
			body: JSON.stringify({ title }),
		});
	},

	/**
	 * Delete a conversation
	 */
	delete: async (id: string): Promise<void> => {
		return fetchApi<void>(`/api/conversations/${id}`, {
			method: 'DELETE',
		});
	},

	/**
	 * Search conversations by message content (Full-text search)
	 * Uses PostgreSQL tsvector with GIN index for high-performance search
	 */
	search: async (query: string, limit: number = 20): Promise<ConversationSearchResponse> => {
		const params = new URLSearchParams({
			q: query,
			limit: limit.toString(),
		});
		return fetchApi<ConversationSearchResponse>(`/api/conversations/search?${params}`, {
			method: 'GET',
		});
	},
};
