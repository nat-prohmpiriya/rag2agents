import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { marked } from 'marked';

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// Configure marked for safe rendering
marked.setOptions({
	gfm: true, // GitHub Flavored Markdown
	breaks: true, // Convert \n to <br>
});

/**
 * Parse markdown to HTML
 */
export function parseMarkdown(content: string): string {
	if (!content) return '';

	try {
		return marked.parse(content, { async: false }) as string;
	} catch (e) {
		console.error('Markdown parse error:', e);
		return content;
	}
}

/**
 * Simple code block detection for syntax highlighting
 */
export function extractCodeBlocks(content: string): { language: string; code: string }[] {
	const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
	const blocks: { language: string; code: string }[] = [];

	let match;
	while ((match = codeBlockRegex.exec(content)) !== null) {
		blocks.push({
			language: match[1] || 'text',
			code: match[2].trim(),
		});
	}

	return blocks;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, "children"> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };
