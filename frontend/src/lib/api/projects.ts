import { fetchApi } from './client';
import type { PaginatedResponse } from './conversations';
import type { Document } from './documents';

export interface Project {
	id: string;
	name: string;
	description: string | null;
	user_id: string;
	created_at: string;
	updated_at: string;
}

export interface ProjectDetail extends Project {
	document_count: number;
	conversation_count: number;
}

export interface ProjectCreate {
	name: string;
	description?: string | null;
}

export interface ProjectUpdate {
	name?: string;
	description?: string | null;
}

export const projectsApi = {
	/**
	 * List projects for current user
	 */
	list: async (page: number = 1, perPage: number = 20): Promise<PaginatedResponse<Project>> => {
		return fetchApi<PaginatedResponse<Project>>(
			`/api/projects?page=${page}&per_page=${perPage}`,
			{ method: 'GET' }
		);
	},

	/**
	 * Get project detail with counts
	 */
	get: async (id: string): Promise<ProjectDetail> => {
		return fetchApi<ProjectDetail>(`/api/projects/${id}`, {
			method: 'GET',
		});
	},

	/**
	 * Create a new project
	 */
	create: async (data: ProjectCreate): Promise<Project> => {
		return fetchApi<Project>('/projects', {
			method: 'POST',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Update a project
	 */
	update: async (id: string, data: ProjectUpdate): Promise<Project> => {
		return fetchApi<Project>(`/api/projects/${id}`, {
			method: 'PATCH',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Delete a project
	 */
	delete: async (id: string): Promise<void> => {
		return fetchApi<void>(`/api/projects/${id}`, {
			method: 'DELETE',
		});
	},

	/**
	 * Assign documents to a project
	 */
	assignDocuments: async (id: string, documentIds: string[]): Promise<void> => {
		return fetchApi<void>(`/api/projects/${id}/documents`, {
			method: 'POST',
			body: JSON.stringify({ document_ids: documentIds }),
		});
	},

	/**
	 * Remove documents from a project
	 */
	removeDocuments: async (id: string, documentIds: string[]): Promise<void> => {
		return fetchApi<void>(`/api/projects/${id}/documents`, {
			method: 'DELETE',
			body: JSON.stringify({ document_ids: documentIds }),
		});
	},

	/**
	 * Get documents in a project
	 */
	getDocuments: async (id: string): Promise<Document[]> => {
		return fetchApi<Document[]>(`/api/projects/${id}/documents`, {
			method: 'GET',
		});
	},
};
