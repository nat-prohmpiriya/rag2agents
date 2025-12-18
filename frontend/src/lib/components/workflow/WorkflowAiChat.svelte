<script lang="ts">
	import { MessageCircle, X, Send, Bot, User, Loader2, Play } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { workflowsApi } from '$lib/api/workflows';
	import { Marked } from 'marked';
	import { markedHighlight } from 'marked-highlight';
	import hljs from 'highlight.js';
	import 'highlight.js/styles/github-dark.css';

	interface Props {
		workflowId: string;
		workflowName?: string;
	}

	let { workflowId, workflowName = 'Workflow' }: Props = $props();

	// State
	let isOpen = $state(false);
	let message = $state('');
	let messages = $state<
		{
			role: 'user' | 'assistant';
			content: string;
			isStreaming?: boolean;
			nodeInfo?: string;
		}[]
	>([]);
	let isLoading = $state(false);
	let currentNode = $state<string | null>(null);
	let textareaRef: HTMLTextAreaElement;
	let messagesContainerRef: HTMLDivElement;
	let abortController: AbortController | null = null;

	// Configure marked
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

	function toggleChat() {
		isOpen = !isOpen;
		if (isOpen && messages.length === 0) {
			// Add welcome message
			messages = [
				{
					role: 'assistant',
					content: `สวัสดี! คุณสามารถพิมพ์ข้อความเพื่อทดสอบ workflow "${workflowName}" ได้เลย ข้อความของคุณจะถูกส่งเข้า workflow และคุณจะเห็นผลลัพธ์แบบ real-time`
				}
			];
		}
	}

	function scrollToBottom() {
		if (messagesContainerRef) {
			requestAnimationFrame(() => {
				messagesContainerRef.scrollTop = messagesContainerRef.scrollHeight;
			});
		}
	}

	async function sendMessage() {
		if (!message.trim() || isLoading) return;

		const userMessage = message.trim();
		message = '';

		// Add user message
		messages = [...messages, { role: 'user', content: userMessage }];
		scrollToBottom();

		// Add placeholder for assistant response
		messages = [...messages, { role: 'assistant', content: '', isStreaming: true }];
		isLoading = true;
		currentNode = null;

		abortController = new AbortController();

		try {
			await workflowsApi.chatStream(
				workflowId,
				userMessage,
				// onChunk
				(content) => {
					messages = messages.map((m, i) =>
						i === messages.length - 1 ? { ...m, content: m.content + content } : m
					);
					scrollToBottom();
				},
				// onNodeEvent
				(event) => {
					currentNode = `${event.node_type}: ${event.status}`;
				},
				// onDone
				() => {
					messages = messages.map((m, i) =>
						i === messages.length - 1 ? { ...m, isStreaming: false } : m
					);
					isLoading = false;
					currentNode = null;
				},
				// onError
				(error) => {
					messages = messages.map((m, i) =>
						i === messages.length - 1
							? { ...m, content: `Error: ${error}`, isStreaming: false }
							: m
					);
					isLoading = false;
					currentNode = null;
				},
				abortController.signal
			);
		} catch (e) {
			if ((e as Error).name !== 'AbortError') {
				messages = messages.map((m, i) =>
					i === messages.length - 1
						? { ...m, content: `Error: ${(e as Error).message}`, isStreaming: false }
						: m
				);
			}
			isLoading = false;
			currentNode = null;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	function handleInput() {
		if (textareaRef) {
			textareaRef.style.height = 'auto';
			textareaRef.style.height = Math.min(textareaRef.scrollHeight, 120) + 'px';
		}
	}

	function stopGeneration() {
		if (abortController) {
			abortController.abort();
			abortController = null;
		}
	}

	function renderMarkdown(content: string): string {
		return markedInstance.parse(content, { async: false }) as string;
	}
</script>

<!-- Floating Button -->
<button
	class="fixed bottom-6 right-6 z-50 flex size-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-all hover:scale-105 hover:bg-primary/90"
	onclick={toggleChat}
>
	{#if isOpen}
		<X class="size-6" />
	{:else}
		<MessageCircle class="size-6" />
	{/if}
</button>

<!-- Chat Window -->
{#if isOpen}
	<div
		class="fixed bottom-6 right-6 top-[calc(3.5rem+1.5rem)] z-50 flex w-[380px] flex-col rounded-2xl border border-border bg-background shadow-2xl"
	>
		<!-- Header -->
		<div class="flex items-center gap-3 border-b border-border px-4 py-3">
			<div class="flex size-9 items-center justify-center rounded-full bg-primary/10">
				<Play class="size-5 text-primary" />
			</div>
			<div class="flex-1">
				<h3 class="font-semibold text-foreground">Test Workflow</h3>
				{#if currentNode}
					<p class="text-xs text-primary animate-pulse">{currentNode}</p>
				{:else}
					<p class="text-xs text-muted-foreground">Chat with your workflow</p>
				{/if}
			</div>
			<Button variant="ghost" size="icon" class="size-8" onclick={toggleChat}>
				<X class="size-4" />
			</Button>
		</div>

		<!-- Messages -->
		<div
			bind:this={messagesContainerRef}
			class="flex-1 space-y-4 overflow-y-auto p-4"
		>
			{#each messages as msg}
				<div class="flex gap-2 {msg.role === 'user' ? 'flex-row-reverse' : ''}">
					<div
						class="flex size-7 shrink-0 items-center justify-center rounded-full {msg.role === 'user'
							? 'bg-secondary'
							: 'bg-primary/10'}"
					>
						{#if msg.role === 'user'}
							<User class="size-4 text-secondary-foreground" />
						{:else}
							<Bot class="size-4 text-primary" />
						{/if}
					</div>
					<div
						class="max-w-[85%] rounded-2xl px-3 py-2 text-sm {msg.role === 'user'
							? 'bg-primary text-primary-foreground rounded-br-sm'
							: 'bg-muted rounded-bl-sm'}"
					>
						{#if msg.role === 'assistant' && !msg.isStreaming}
							<div class="prose prose-sm dark:prose-invert max-w-none">
								{@html renderMarkdown(msg.content)}
							</div>
						{:else}
							<p class="whitespace-pre-wrap">{msg.content}</p>
						{/if}
						{#if msg.isStreaming && !msg.content}
							<div class="flex items-center gap-1">
								<span
									class="size-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.3s]"
								></span>
								<span
									class="size-1.5 animate-bounce rounded-full bg-current [animation-delay:-0.15s]"
								></span>
								<span class="size-1.5 animate-bounce rounded-full bg-current"></span>
							</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>

		<!-- Input -->
		<div class="border-t border-border p-3">
			<div class="flex items-end gap-2">
				<textarea
					bind:this={textareaRef}
					bind:value={message}
					placeholder="Type a message to test workflow..."
					rows="1"
					class="max-h-[120px] min-h-[40px] flex-1 resize-none rounded-xl border border-border bg-muted/50 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
					onkeydown={handleKeydown}
					oninput={handleInput}
					disabled={isLoading}
				></textarea>
				{#if isLoading}
					<Button
						size="icon"
						class="size-10 shrink-0 rounded-xl"
						variant="destructive"
						onclick={stopGeneration}
					>
						<Loader2 class="size-4 animate-spin" />
					</Button>
				{:else}
					<Button
						size="icon"
						class="size-10 shrink-0 rounded-xl"
						onclick={sendMessage}
						disabled={!message.trim()}
					>
						<Send class="size-4" />
					</Button>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.prose :global(p) {
		margin-bottom: 0.5rem;
	}
	.prose :global(p:last-child) {
		margin-bottom: 0;
	}
	.prose :global(ul),
	.prose :global(ol) {
		margin: 0.5rem 0;
		padding-left: 1rem;
	}
	.prose :global(li) {
		margin: 0.125rem 0;
	}
	.prose :global(code) {
		background-color: hsl(var(--muted));
		padding: 0.125rem 0.25rem;
		border-radius: 0.25rem;
		font-size: 0.75em;
	}
	.prose :global(pre) {
		background-color: hsl(220 13% 18%);
		padding: 0.75rem;
		border-radius: 0.5rem;
		overflow-x: auto;
		margin: 0.5rem 0;
	}
	.prose :global(pre code) {
		background: none;
		padding: 0;
		color: #e5e5e5;
	}
</style>
