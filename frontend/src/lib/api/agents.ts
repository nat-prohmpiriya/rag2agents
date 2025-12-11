import { fetchApi } from './client';

export interface AgentInfo {
	id?: string;
	user_id?: string;
	project_id?: string;
	name: string;
	slug: string;
	icon?: string;
	description?: string;
	tools: string[];
	config?: Record<string, unknown>;
	is_active: boolean;
	source: 'system' | 'user';
	document_ids?: string[];
	created_at?: string;
	updated_at?: string;
}

export interface AgentDetail extends AgentInfo {
	system_prompt?: string;
}

export interface AgentCreate {
	name: string;
	slug: string;
	description?: string;
	icon?: string;
	system_prompt?: string;
	tools?: string[];
	config?: Record<string, unknown>;
	is_active?: boolean;
	project_id?: string;
	document_ids?: string[];
}

export interface AgentUpdate {
	name?: string;
	slug?: string;
	description?: string;
	icon?: string;
	system_prompt?: string;
	tools?: string[];
	config?: Record<string, unknown>;
	is_active?: boolean;
	project_id?: string;
	document_ids?: string[];
}

export interface ToolInfo {
	name: string;
	description: string;
}

export interface AgentListResponse {
	agents: AgentInfo[];
	total: number;
}

export interface AgentToolsResponse {
	agent_slug: string;
	tools: ToolInfo[];
}

export const agentsApi = {
	/**
	 * List all available agents
	 */
	list: async (): Promise<AgentListResponse> => {
		return fetchApi<AgentListResponse>('/agents', {
			method: 'GET',
		});
	},

	/**
	 * Get agent detail by slug
	 */
	get: async (slug: string): Promise<AgentDetail> => {
		return fetchApi<AgentDetail>(`/api/agents/${slug}`, {
			method: 'GET',
		});
	},

	/**
	 * Get tools available for an agent
	 */
	getTools: async (slug: string): Promise<AgentToolsResponse> => {
		return fetchApi<AgentToolsResponse>(`/api/agents/${slug}/tools`, {
			method: 'GET',
		});
	},

	/**
	 * Create a new user agent
	 */
	create: async (data: AgentCreate): Promise<AgentInfo> => {
		return fetchApi<AgentInfo>('/agents', {
			method: 'POST',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Update a user agent
	 */
	update: async (agentId: string, data: AgentUpdate): Promise<AgentInfo> => {
		return fetchApi<AgentInfo>(`/api/agents/${agentId}`, {
			method: 'PUT',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Delete a user agent
	 */
	delete: async (agentId: string): Promise<void> => {
		return fetchApi<void>(`/api/agents/${agentId}`, {
			method: 'DELETE',
		});
	},
};
