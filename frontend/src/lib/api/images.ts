import { fetchApi } from './client';

export interface ImageModel {
	id: string;
	name: string;
	provider: string;
	description: string | null;
}

export interface ImageSize {
	value: string;
	label: string;
}

export interface ImageData {
	id: string;
	url: string;
	b64_json: string | null;
	revised_prompt: string | null;
}

export interface ImageGenerateRequest {
	prompt: string;
	model?: string;
	size?: string;
	n?: number;
}

export interface ImageHistoryItem {
	id: string;
	prompt: string;
	revised_prompt: string | null;
	model: string;
	size: string;
	image_url: string;
	file_size: number | null;
	created_at: string;
}

export interface ImageHistoryResponse {
	images: ImageHistoryItem[];
	total: number;
	limit: number;
	offset: number;
}

export interface ImageGenerateResponse {
	id: string;
	created: string;
	model: string;
	prompt: string;
	size: string;
	images: ImageData[];
}

export interface ImageModelsResponse {
	models: ImageModel[];
}

export interface ImageSizesResponse {
	sizes: ImageSize[];
}

/**
 * Get available image generation models
 */
export async function getImageModels(): Promise<ImageModelsResponse> {
	return fetchApi<ImageModelsResponse>('/images/models');
}

/**
 * Get available image sizes
 */
export async function getImageSizes(): Promise<ImageSizesResponse> {
	return fetchApi<ImageSizesResponse>('/images/sizes');
}

/**
 * Generate an image from a text prompt
 */
export async function generateImage(request: ImageGenerateRequest): Promise<ImageGenerateResponse> {
	return fetchApi<ImageGenerateResponse>('/images/generate', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}

/**
 * Get user's image generation history
 */
export async function getImageHistory(limit: number = 50, offset: number = 0): Promise<ImageHistoryResponse> {
	return fetchApi<ImageHistoryResponse>(`/images/history?limit=${limit}&offset=${offset}`);
}

/**
 * Delete a generated image
 */
export async function deleteImage(imageId: string): Promise<{ deleted: boolean; id: string }> {
	return fetchApi<{ deleted: boolean; id: string }>(`/images/${imageId}`, {
		method: 'DELETE'
	});
}
