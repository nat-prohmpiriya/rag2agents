<script lang="ts">
	import { User, Bot, Copy, Check, RefreshCw, Pencil, X, ThumbsUp, ThumbsDown, Bug } from 'lucide-svelte';
	import DebugPanel from './DebugPanel.svelte';
	import { cn } from '$lib/utils';
	import { Marked } from 'marked';
	import { markedHighlight } from 'marked-highlight';
	import hljs from 'highlight.js';
	import 'highlight.js/styles/github-dark.css';
	import type { SourceInfo, UsageInfo, LatencyInfo } from '$lib/api/chat';
	import { Button } from '$lib/components/ui/button';
	import * as Avatar from '$lib/components/ui/avatar';

	// Configure marked with highlight.js
	const markedInstance = new Marked(
		markedHighlight({
			emptyLangClass: 'hljs',
			langPrefix: 'hljs language-',
			highlight(code, lang) {
				const language = hljs.getLanguage(lang) ? lang : 'plaintext';
				return hljs.highlight(code, { language }).value;
			}
		})
	);

	markedInstance.setOptions({
		breaks: true,
		gfm: true
	});

	interface Props {
		role: 'user' | 'assistant';
		content: string;
		isStreaming?: boolean;
		isThinking?: boolean;
		sources?: SourceInfo[];
		usage?: UsageInfo;
		latency?: LatencyInfo;
		createdAt?: Date;
		isLastAssistant?: boolean;
		isLastUser?: boolean;
		images?: string[]; // base64 previews for user messages
		onRegenerate?: () => void;
		onEdit?: (newContent: string) => void;
	}

	let {
		role,
		content,
		isStreaming = false,
		isThinking = false,
		sources = [],
		usage,
		latency,
		createdAt,
		isLastAssistant = false,
		isLastUser = false,
		images = [],
		onRegenerate,
		onEdit
	}: Props = $props();

	let isUser = $derived(role === 'user');

	// Render markdown to HTML (skip during streaming for performance)
	let renderedContent = $derived(
		isUser ? content : isStreaming ? content : (markedInstance.parse(content, { async: false }) as string)
	);

	// Copy button state
	let copied = $state(false);

	// Edit mode state
	let isEditing = $state(false);
	let editContent = $state('');

	// Debug panel state
	let showDebugPanel = $state(false);

	// Check if debug info is available
	let hasDebugInfo = $derived(
		(sources && sources.length > 0) || usage || latency
	);

	async function handleCopy() {
		await navigator.clipboard.writeText(content);
		copied = true;
		setTimeout(() => {
			copied = false;
		}, 2000);
	}

	function startEdit() {
		editContent = content;
		isEditing = true;
	}

	function cancelEdit() {
		isEditing = false;
		editContent = '';
	}

	function submitEdit() {
		if (editContent.trim() && editContent !== content) {
			onEdit?.(editContent.trim());
		}
		isEditing = false;
		editContent = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			submitEdit();
		} else if (e.key === 'Escape') {
			cancelEdit();
		}
	}
</script>

<div class="w-full max-w-3xl mx-auto px-4 py-4">
	{#if isUser}
		<!-- User message - right aligned with avatar -->
		<div class="flex justify-end gap-3">
			<div class="max-w-[80%]">
				{#if isEditing}
					<div class="flex flex-col gap-2 bg-muted rounded-2xl p-4">
						<textarea
							bind:value={editContent}
							onkeydown={handleKeydown}
							class="w-full min-h-[60px] p-2 rounded bg-background resize-none focus:outline-none focus:ring-1 focus:ring-primary"
							rows="3"
						></textarea>
						<div class="flex justify-end gap-2">
							<Button variant="ghost" size="sm" onclick={cancelEdit}>
								Cancel
							</Button>
							<Button size="sm" onclick={submitEdit}>
								Save & Send
							</Button>
						</div>
					</div>
				{:else}
					<div class="group relative">
						<div class="bg-primary text-primary-foreground rounded-2xl rounded-br-sm px-4 py-3">
							<!-- Images -->
							{#if images && images.length > 0}
								<div class="flex gap-2 mb-2 flex-wrap">
									{#each images as img}
										<img
											src={img}
											alt="Uploaded image"
											class="h-20 w-20 rounded-lg object-cover border border-primary-foreground/20"
										/>
									{/each}
								</div>
							{/if}
							<p class="whitespace-pre-wrap break-words">{content}</p>
						</div>
						<!-- Edit button on hover -->
						{#if isLastUser && onEdit}
							<div class="absolute -bottom-8 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
								<Button
									variant="ghost"
									size="sm"
									class="h-7 text-xs text-muted-foreground"
									onclick={startEdit}
								>
									<Pencil class="size-3 mr-1" />
									Edit
								</Button>
							</div>
						{/if}
					</div>
				{/if}
			</div>
			<!-- User Avatar -->
			<Avatar.Root class="size-8 shrink-0">
				<Avatar.Fallback class="bg-secondary text-secondary-foreground">
					<User class="size-4" />
				</Avatar.Fallback>
			</Avatar.Root>
		</div>
	{:else}
		<!-- Assistant message - left aligned with avatar -->
		<div class="flex gap-3">
			<!-- Bot Avatar -->
			<Avatar.Root class="size-8 shrink-0">
				<Avatar.Fallback class="bg-primary text-primary-foreground">
					<Bot class="size-4" />
				</Avatar.Fallback>
			</Avatar.Root>

			<div class="flex-1 group min-w-0">
				{#if isThinking && !content}
					<!-- Thinking animation (three bouncing dots) -->
					<div class="flex items-center gap-1 py-3">
						<span class="size-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]"></span>
						<span class="size-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]"></span>
						<span class="size-2 rounded-full bg-muted-foreground animate-bounce"></span>
					</div>
				{:else}
					<div class="prose prose-sm dark:prose-invert max-w-none">
						{#if isStreaming}
							<p class="whitespace-pre-wrap break-words">{content}</p>
						{:else}
							{@html renderedContent}
						{/if}
					</div>

					<!-- Action buttons below message -->
					{#if !isStreaming && !isThinking}
						<div class="flex items-center gap-1 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
							<Button
								variant="ghost"
								size="icon"
								class="size-8 text-muted-foreground hover:text-foreground"
								onclick={handleCopy}
								title="Copy"
							>
								{#if copied}
									<Check class="size-4" />
								{:else}
									<Copy class="size-4" />
								{/if}
							</Button>
							{#if isLastAssistant && onRegenerate}
								<Button
									variant="ghost"
									size="icon"
									class="size-8 text-muted-foreground hover:text-foreground"
									onclick={onRegenerate}
									title="Regenerate"
								>
									<RefreshCw class="size-4" />
								</Button>
							{/if}
							<Button
								variant="ghost"
								size="icon"
								class="size-8 text-muted-foreground hover:text-foreground"
								title="Good response"
							>
								<ThumbsUp class="size-4" />
							</Button>
							<Button
								variant="ghost"
								size="icon"
								class="size-8 text-muted-foreground hover:text-foreground"
								title="Bad response"
							>
								<ThumbsDown class="size-4" />
							</Button>
							{#if hasDebugInfo}
								<Button
									variant="ghost"
									size="icon"
									class="size-8 text-muted-foreground hover:text-foreground {showDebugPanel ? 'bg-muted' : ''}"
									onclick={() => (showDebugPanel = !showDebugPanel)}
									title="Debug info"
								>
									<Bug class="size-4" />
								</Button>
							{/if}
						</div>
					{/if}

					<!-- Debug Panel -->
					{#if showDebugPanel && hasDebugInfo}
						<DebugPanel {sources} {usage} {latency} />
					{/if}
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	/* Markdown content styles */
	.prose :global(p) {
		margin-bottom: 1rem;
	}
	.prose :global(p:last-child) {
		margin-bottom: 0;
	}
	.prose :global(ul),
	.prose :global(ol) {
		margin: 1rem 0;
		padding-left: 1.5rem;
	}
	.prose :global(li) {
		margin: 0.25rem 0;
	}
	.prose :global(code) {
		background-color: hsl(var(--muted));
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-size: 0.875em;
	}
	.prose :global(pre) {
		background-color: hsl(220 13% 18%);
		padding: 1rem;
		border-radius: 0.75rem;
		overflow-x: auto;
		margin: 1rem 0;
	}
	.prose :global(pre code) {
		background: none;
		padding: 0;
		color: #e5e5e5;
	}
	.prose :global(strong) {
		font-weight: 600;
	}
	.prose :global(h1),
	.prose :global(h2),
	.prose :global(h3),
	.prose :global(h4) {
		font-weight: 600;
		margin: 1.5rem 0 0.75rem 0;
	}
	.prose :global(h1) {
		font-size: 1.5rem;
	}
	.prose :global(h2) {
		font-size: 1.25rem;
	}
	.prose :global(h3) {
		font-size: 1.125rem;
	}
	.prose :global(blockquote) {
		border-left: 3px solid hsl(var(--border));
		padding-left: 1rem;
		margin: 1rem 0;
		color: hsl(var(--muted-foreground));
	}
</style>
