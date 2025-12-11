import { fetchApi } from './client';

// =============================================================================
// Types
// =============================================================================

export interface NodePosition {
	x: number;
	y: number;
}

export interface NodeData {
	label: string;
	type: string;
	config: Record<string, unknown>;
}

export interface WorkflowNode {
	id: string;
	type: string;
	position: NodePosition;
	data: NodeData;
	width?: number;
	height?: number;
}

export interface WorkflowEdge {
	id: string;
	source: string;
	target: string;
	sourceHandle?: string;
	targetHandle?: string;
	type?: string;
	animated?: boolean;
	label?: string;
}

export interface Viewport {
	x: number;
	y: number;
	zoom: number;
}

export type WorkflowStatus = 'draft' | 'active' | 'archived';
export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface WorkflowInfo {
	id: string;
	user_id: string;
	name: string;
	description?: string;
	nodes: WorkflowNode[];
	edges: WorkflowEdge[];
	viewport?: Viewport;
	status: WorkflowStatus;
	is_template: boolean;
	config?: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

export interface WorkflowCreate {
	name: string;
	description?: string;
	nodes?: WorkflowNode[];
	edges?: WorkflowEdge[];
	viewport?: Viewport;
	is_template?: boolean;
	config?: Record<string, unknown>;
}

export interface WorkflowUpdate {
	name?: string;
	description?: string;
	nodes?: WorkflowNode[];
	edges?: WorkflowEdge[];
	viewport?: Viewport;
	status?: WorkflowStatus;
	is_template?: boolean;
	config?: Record<string, unknown>;
}

export interface WorkflowListResponse {
	workflows: WorkflowInfo[];
	total: number;
	page: number;
	page_size: number;
}

export interface NodeExecutionLog {
	node_id: string;
	node_type: string;
	status: string;
	started_at?: string;
	completed_at?: string;
	input?: Record<string, unknown>;
	output?: Record<string, unknown>;
	error?: string;
	tokens_used: number;
}

export interface WorkflowExecutionInfo {
	id: string;
	workflow_id: string;
	user_id: string;
	status: ExecutionStatus;
	inputs?: Record<string, unknown>;
	outputs?: Record<string, unknown>;
	node_states?: Record<string, unknown>;
	current_node_id?: string;
	error_message?: string;
	logs: NodeExecutionLog[];
	started_at?: string;
	completed_at?: string;
	total_tokens: number;
	created_at: string;
	updated_at: string;
}

export interface WorkflowExecutionListResponse {
	executions: WorkflowExecutionInfo[];
	total: number;
	page: number;
	page_size: number;
}

export interface WorkflowExecuteRequest {
	inputs: Record<string, unknown>;
}

// =============================================================================
// API Client
// =============================================================================

export const workflowsApi = {
	/**
	 * List all workflows
	 */
	list: async (page = 1, pageSize = 20): Promise<WorkflowListResponse> => {
		return fetchApi<WorkflowListResponse>(`/workflows?page=${page}&page_size=${pageSize}`, {
			method: 'GET'
		});
	},

	/**
	 * Get workflow by ID
	 */
	get: async (workflowId: string): Promise<WorkflowInfo> => {
		return fetchApi<WorkflowInfo>(`/workflows/${workflowId}`, {
			method: 'GET'
		});
	},

	/**
	 * Create a new workflow
	 */
	create: async (data: WorkflowCreate): Promise<WorkflowInfo> => {
		return fetchApi<WorkflowInfo>('/workflows', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	},

	/**
	 * Update a workflow
	 */
	update: async (workflowId: string, data: WorkflowUpdate): Promise<WorkflowInfo> => {
		return fetchApi<WorkflowInfo>(`/workflows/${workflowId}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	},

	/**
	 * Delete a workflow
	 */
	delete: async (workflowId: string): Promise<void> => {
		return fetchApi<void>(`/workflows/${workflowId}`, {
			method: 'DELETE'
		});
	},

	/**
	 * Duplicate a workflow
	 */
	duplicate: async (workflowId: string): Promise<WorkflowInfo> => {
		return fetchApi<WorkflowInfo>(`/workflows/${workflowId}/duplicate`, {
			method: 'POST'
		});
	},

	/**
	 * Execute a workflow
	 */
	execute: async (workflowId: string, inputs: Record<string, unknown>): Promise<WorkflowExecutionInfo> => {
		return fetchApi<WorkflowExecutionInfo>(`/workflows/${workflowId}/execute`, {
			method: 'POST',
			body: JSON.stringify({ inputs })
		});
	},

	/**
	 * List workflow executions
	 */
	listExecutions: async (
		workflowId: string,
		page = 1,
		pageSize = 20
	): Promise<WorkflowExecutionListResponse> => {
		return fetchApi<WorkflowExecutionListResponse>(
			`/workflows/${workflowId}/executions?page=${page}&page_size=${pageSize}`,
			{ method: 'GET' }
		);
	},

	/**
	 * Get execution by ID
	 */
	getExecution: async (executionId: string): Promise<WorkflowExecutionInfo> => {
		return fetchApi<WorkflowExecutionInfo>(`/workflows/executions/${executionId}`, {
			method: 'GET'
		});
	},

	/**
	 * Cancel a running execution
	 */
	cancelExecution: async (executionId: string): Promise<WorkflowExecutionInfo> => {
		return fetchApi<WorkflowExecutionInfo>(`/workflows/executions/${executionId}/cancel`, {
			method: 'POST'
		});
	}
};
