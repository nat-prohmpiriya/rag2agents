import { fetchApi, uploadFile } from './client';
import type { PaginatedResponse } from './conversations';

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'error';

export interface Document {
	id: string;
	filename: string;
	file_type: string;
	file_size: number;
	status: DocumentStatus;
	chunk_count: number;
	description: string | null;
	tags: string[] | null;
	created_at: string;
}

export interface DocumentDetail extends Document {
	error_message: string | null;
}

export interface DocumentUpdate {
	filename?: string;
	description?: string | null;
	tags?: string[] | null;
}

export const documentsApi = {
	/**
	 * Upload a document file
	 */
	upload: async (file: File, onProgress?: (percent: number) => void): Promise<Document> => {
		return uploadFile<Document>('/documents', file, onProgress);
	},

	/**
	 * List documents for current user
	 */
	list: async (page: number = 1, perPage: number = 20): Promise<PaginatedResponse<Document>> => {
		return fetchApi<PaginatedResponse<Document>>(
			`/api/documents?page=${page}&per_page=${perPage}`,
			{ method: 'GET' }
		);
	},

	/**
	 * Get document detail
	 */
	get: async (id: string): Promise<DocumentDetail> => {
		return fetchApi<DocumentDetail>(`/api/documents/${id}`, {
			method: 'GET',
		});
	},

	/**
	 * Update document metadata
	 */
	update: async (id: string, data: DocumentUpdate): Promise<Document> => {
		return fetchApi<Document>(`/api/documents/${id}`, {
			method: 'PATCH',
			body: JSON.stringify(data),
		});
	},

	/**
	 * Delete a document
	 */
	delete: async (id: string): Promise<void> => {
		return fetchApi<void>(`/api/documents/${id}`, {
			method: 'DELETE',
		});
	},
};
