<script lang="ts">
	import { onMount } from 'svelte';
	import { chatApi, type ModelInfo, type SourceInfo } from '$lib/api/chat';
	import { Button } from '$lib/components/ui/button';
	import { ArrowDown, FileText, Send, Square, Loader2 } from 'lucide-svelte';
	import ChatMessage from '$lib/components/llm-chat2/ChatMessage.svelte';
	import * as Select from '$lib/components/ui/select';

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		createdAt: Date;
		sources?: SourceInfo[];
	}

	interface Props {
		documentId: string;
		documentName: string;
	}

	let { documentId, documentName }: Props = $props();

	// State
	let models = $state<ModelInfo[]>([]);
	let selectedModel = $state<ModelInfo | null>(null);
	let messages = $state<Message[]>([]);
	let inputValue = $state('');
	let isLoading = $state(false);
	let isStreaming = $state(false);
	let streamingContent = $state('');
	let error = $state<string | null>(null);
	let messagesContainer = $state<HTMLDivElement | null>(null);
	let showScrollButton = $state(false);
	let conversationId = $state<string | undefined>(undefined);
	let abortController = $state<AbortController | null>(null);
	let textareaEl = $state<HTMLTextAreaElement | null>(null);

	onMount(async () => {
		await loadModels();
	});

	async function loadModels() {
		try {
			const response = await chatApi.getModels();
			models = response.models;
			// Default to Gemini 2.5 Flash
			selectedModel =
				models.find((m) => m.id.includes('gemini-2.5-flash') || m.id.includes('gemini-2.0-flash')) ||
				models.find((m) => m.id.includes('gemini')) ||
				models[0] ||
				null;
		} catch (e) {
			console.error('Failed to load models:', e);
			error = 'Failed to load models';
		}
	}

	async function handleSend() {
		const message = inputValue.trim();
		if (!message || !selectedModel || isLoading) return;

		const userMessage: Message = {
			id: crypto.randomUUID(),
			role: 'user',
			content: message,
			createdAt: new Date()
		};

		messages = [...messages, userMessage];
		inputValue = '';
		isLoading = true;
		isStreaming = true;
		streamingContent = '';
		error = null;

		// Reset textarea height
		if (textareaEl) {
			textareaEl.style.height = 'auto';
		}

		abortController = new AbortController();
		scrollToBottom();

		try {
			await chatApi.stream(
				{
					message,
					model: selectedModel.id,
					conversation_id: conversationId,
					stream: true,
					use_rag: true,
					rag_document_ids: [documentId]
				},
				(content) => {
					streamingContent += content;
					scrollToBottom();
				},
				(newConversationId, sources) => {
					const assistantMessage: Message = {
						id: crypto.randomUUID(),
						role: 'assistant',
						content: streamingContent,
						createdAt: new Date(),
						sources
					};
					messages = [...messages, assistantMessage];
					streamingContent = '';
					isStreaming = false;
					isLoading = false;
					abortController = null;

					if (newConversationId && !conversationId) {
						conversationId = newConversationId;
					}
				},
				(errorMsg) => {
					error = errorMsg;
					isStreaming = false;
					isLoading = false;
					abortController = null;
				},
				abortController.signal
			);
		} catch (e) {
			if (e instanceof Error && e.name === 'AbortError') {
				if (streamingContent) {
					const assistantMessage: Message = {
						id: crypto.randomUUID(),
						role: 'assistant',
						content: streamingContent,
						createdAt: new Date()
					};
					messages = [...messages, assistantMessage];
				}
				streamingContent = '';
				isStreaming = false;
				isLoading = false;
				abortController = null;
				return;
			}
			console.error('Chat error:', e);
			error = e instanceof Error ? e.message : 'Failed to send message';
			isStreaming = false;
			isLoading = false;
			abortController = null;
		}
	}

	function handleStop() {
		if (abortController) {
			abortController.abort();
		}
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	function handleInput(e: Event) {
		const target = e.target as HTMLTextAreaElement;
		target.style.height = 'auto';
		target.style.height = Math.min(target.scrollHeight, 200) + 'px';
	}

	let scrollTimeout: ReturnType<typeof setTimeout> | null = null;
	function scrollToBottom() {
		if (scrollTimeout) return;
		scrollTimeout = setTimeout(() => {
			if (messagesContainer) {
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}
			scrollTimeout = null;
		}, 50);
	}

	function handleScroll() {
		if (!messagesContainer) return;
		const { scrollTop, scrollHeight, clientHeight } = messagesContainer;
		const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
		showScrollButton = distanceFromBottom > 100;
	}

	function handleModelChange(value: string | undefined) {
		if (value) {
			selectedModel = models.find((m) => m.id === value) || null;
		}
	}
</script>

<div class="flex h-full flex-col bg-background">
	<!-- Header -->
	<div class="shrink-0 border-b px-4 py-3">
		<div class="flex items-center gap-2">
			<FileText class="size-4 text-muted-foreground" />
			<span class="text-sm font-medium truncate">{documentName}</span>
		</div>
		<p class="mt-1 text-xs text-muted-foreground">
			Ask questions about this document
		</p>
	</div>

	<!-- Messages -->
	<div
		bind:this={messagesContainer}
		class="flex-1 overflow-y-auto"
		onscroll={handleScroll}
	>
		{#if messages.length === 0 && !isStreaming}
			<div class="flex h-full items-center justify-center p-4">
				<div class="text-center">
					<FileText class="mx-auto size-12 text-muted-foreground/50" />
					<h3 class="mt-4 text-sm font-medium">Chat with your document</h3>
					<p class="mt-1 text-xs text-muted-foreground">
						Ask questions and get answers based on the document content.
					</p>
				</div>
			</div>
		{:else}
			<div class="py-4">
				{#each messages as message (message.id)}
					<ChatMessage
						role={message.role}
						content={message.content}
						sources={message.sources}
						createdAt={message.createdAt}
					/>
				{/each}

				{#if isStreaming}
					<ChatMessage
						role="assistant"
						content={streamingContent}
						isStreaming={true}
						isThinking={!streamingContent}
					/>
				{/if}

				{#if error}
					<div class="mx-4 my-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
						{error}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Scroll button -->
	{#if showScrollButton}
		<Button
			variant="outline"
			size="icon"
			class="absolute bottom-32 right-4 size-8 rounded-full shadow-lg"
			onclick={scrollToBottom}
		>
			<ArrowDown class="size-4" />
		</Button>
	{/if}

	<!-- Input Area -->
	<div class="shrink-0 border-t p-3">
		<!-- Model selector -->
		<div class="mb-2">
			<Select.Root type="single" value={selectedModel?.id} onValueChange={handleModelChange}>
				<Select.Trigger class="h-8 text-xs">
					<span class="truncate">{selectedModel?.name || 'Select model'}</span>
				</Select.Trigger>
				<Select.Content>
					{#each models as model (model.id)}
						<Select.Item value={model.id} class="text-xs">
							{model.name}
						</Select.Item>
					{/each}
				</Select.Content>
			</Select.Root>
		</div>

		<!-- Input -->
		<div class="flex gap-2">
			<textarea
				bind:this={textareaEl}
				bind:value={inputValue}
				onkeydown={handleKeyDown}
				oninput={handleInput}
				placeholder="Ask about this document..."
				class="flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
				rows="1"
				disabled={isLoading || !selectedModel}
			></textarea>
			{#if isLoading}
				<Button size="icon" variant="destructive" onclick={handleStop}>
					<Square class="size-4" />
				</Button>
			{:else}
				<Button
					size="icon"
					onclick={handleSend}
					disabled={!inputValue.trim() || !selectedModel}
				>
					{#if isLoading}
						<Loader2 class="size-4 animate-spin" />
					{:else}
						<Send class="size-4" />
					{/if}
				</Button>
			{/if}
		</div>
	</div>
</div>
