<script lang="ts">
	import { onMount } from 'svelte';
	import { chatApi, type ModelInfo, type SourceInfo, type UsageInfo, type LatencyInfo } from '$lib/api/chat';
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ChatMessage from './ChatMessage.svelte';
	import { Button } from '$lib/components/ui/button';
	import { ArrowDown } from 'lucide-svelte';
	import type { Message as ApiMessage } from '$lib/api/conversations';

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		createdAt: Date;
		sources?: SourceInfo[];
		usage?: UsageInfo;
		latency?: LatencyInfo;
	}

	interface Props {
		conversationId?: string;
		conversationTitle?: string;
		initialMessages?: ApiMessage[];
		initialModel?: string;
		agentSlug?: string;
		onConversationCreated?: (id: string) => void;
		onNewChat?: () => void;
		onDelete?: () => void;
	}

	let {
		conversationId = $bindable(),
		conversationTitle = 'New conversation',
		initialMessages = [],
		initialModel,
		agentSlug,
		onConversationCreated,
		onNewChat,
		onDelete
	}: Props = $props();

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

	// Abort controller for stopping streaming
	let abortController = $state<AbortController | null>(null);

	// Convert initial messages to local format
	$effect(() => {
		if (initialMessages.length > 0) {
			messages = initialMessages.map((m) => ({
				id: m.id,
				role: m.role as 'user' | 'assistant',
				content: m.content,
				createdAt: new Date(m.created_at)
			}));
			// Scroll to bottom after loading messages
			scrollToBottom();
		} else {
			messages = [];
		}
	});

	// Load models on mount
	onMount(async () => {
		await loadModels();
	});

	async function loadModels() {
		try {
			const response = await chatApi.getModels();
			models = response.models;

			// Select initial model or default to Gemini 2.5 Flash
			if (initialModel) {
				selectedModel = models.find((m) => m.id === initialModel) || models[0] || null;
			} else {
				// Default to Gemini 2.5 Flash
				selectedModel = models.find((m) => m.id.includes('gemini-2.5-flash') || m.id.includes('gemini-2.0-flash'))
					|| models.find((m) => m.id.includes('gemini'))
					|| models[0] || null;
			}
		} catch (e) {
			console.error('Failed to load models:', e);
			error = 'Failed to load models';
		}
	}

	function handleModelSelect(model: ModelInfo) {
		selectedModel = model;
	}

	async function handleSend(message: string) {
		if (!selectedModel || isLoading) return;

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

		// Create abort controller for this request
		abortController = new AbortController();

		// Scroll to bottom
		scrollToBottom();

		try {
			await chatApi.stream(
				{
					message,
					model: selectedModel.id,
					conversation_id: conversationId,
					agent_slug: agentSlug,
					stream: true
				},
				(content) => {
					streamingContent += content;
					scrollToBottom();
				},
				(doneData) => {
					// On done - add assistant message with sources, usage, and latency
					const assistantMessage: Message = {
						id: crypto.randomUUID(),
						role: 'assistant',
						content: streamingContent,
						createdAt: new Date(),
						sources: doneData.sources,
						usage: doneData.usage,
						latency: doneData.latency
					};
					messages = [...messages, assistantMessage];
					streamingContent = '';
					isStreaming = false;
					isLoading = false;
					abortController = null;

					// If this was a new conversation, notify parent
					if (doneData.conversation_id && !conversationId) {
						conversationId = doneData.conversation_id;
						onConversationCreated?.(doneData.conversation_id);
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
			// Ignore abort errors
			if (e instanceof Error && e.name === 'AbortError') {
				// Save partial response if any
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

	// Regenerate last assistant response
	async function handleRegenerate() {
		if (!selectedModel || isLoading || messages.length < 2) return;

		// Find last user message
		let lastUserMessage: Message | null = null;
		for (let i = messages.length - 1; i >= 0; i--) {
			if (messages[i].role === 'user') {
				lastUserMessage = messages[i];
				break;
			}
		}

		if (!lastUserMessage) return;

		// Remove last assistant message from UI
		const lastMessage = messages[messages.length - 1];
		if (lastMessage.role === 'assistant') {
			messages = messages.slice(0, -1);
		}

		// Resend with skip_user_save flag
		isLoading = true;
		isStreaming = true;
		streamingContent = '';
		error = null;

		scrollToBottom();

		try {
			await chatApi.stream(
				{
					message: lastUserMessage.content,
					model: selectedModel.id,
					conversation_id: conversationId,
					agent_slug: agentSlug,
					stream: true,
					skip_user_save: true
				},
				(content) => {
					streamingContent += content;
					scrollToBottom();
				},
				(doneData) => {
					const assistantMessage: Message = {
						id: crypto.randomUUID(),
						role: 'assistant',
						content: streamingContent,
						createdAt: new Date(),
						sources: doneData.sources,
						usage: doneData.usage,
						latency: doneData.latency
					};
					messages = [...messages, assistantMessage];
					streamingContent = '';
					isStreaming = false;
					isLoading = false;
				},
				(errorMsg) => {
					error = errorMsg;
					isStreaming = false;
					isLoading = false;
				}
			);
		} catch (e) {
			console.error('Regenerate error:', e);
			error = e instanceof Error ? e.message : 'Failed to regenerate response';
			isStreaming = false;
			isLoading = false;
		}
	}

	// Edit last user message and resend
	async function handleEdit(newContent: string) {
		if (!selectedModel || isLoading || messages.length < 1) return;

		// Find and update last user message
		let lastUserIndex = -1;
		for (let i = messages.length - 1; i >= 0; i--) {
			if (messages[i].role === 'user') {
				lastUserIndex = i;
				break;
			}
		}

		if (lastUserIndex === -1) return;

		// Remove messages from last user message onwards
		messages = messages.slice(0, lastUserIndex);

		// Send edited message as new
		await handleSend(newContent);
	}

	// Check if message is the last assistant message
	function isLastAssistantMessage(index: number): boolean {
		if (messages[index].role !== 'assistant') return false;
		for (let i = index + 1; i < messages.length; i++) {
			if (messages[i].role === 'assistant') return false;
		}
		return true;
	}

	// Check if message is the last user message
	function isLastUserMessage(index: number): boolean {
		if (messages[index].role !== 'user') return false;
		for (let i = index + 1; i < messages.length; i++) {
			if (messages[i].role === 'user') return false;
		}
		return true;
	}

	// Scroll handling
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
</script>

<div class="flex h-full flex-col bg-background overflow-hidden relative">
	<!-- Header (sticky top) -->
	<div class="shrink-0 sticky top-0 z-10">
		<ChatHeader title={conversationTitle} onDelete={onDelete} />
	</div>

	<!-- Messages Area (scrollable) -->
	<div
		bind:this={messagesContainer}
		class="flex-1 overflow-y-auto min-h-0"
		onscroll={handleScroll}
	>
		{#if messages.length === 0 && !isStreaming}
			<!-- Empty state -->
			<div class="flex h-full items-center justify-center">
				<div class="text-center">
					<h2 class="text-2xl font-medium mb-2">How can I help you today?</h2>
					<p class="text-muted-foreground">Start a conversation by typing a message below.</p>
				</div>
			</div>
		{:else}
			<!-- Messages -->
			<div class="py-4">
				{#each messages as message, index (message.id)}
					<ChatMessage
						role={message.role}
						content={message.content}
						sources={message.sources}
						usage={message.usage}
						latency={message.latency}
						createdAt={message.createdAt}
						isLastAssistant={isLastAssistantMessage(index)}
						isLastUser={isLastUserMessage(index)}
						onRegenerate={isLastAssistantMessage(index) ? handleRegenerate : undefined}
						onEdit={isLastUserMessage(index) ? handleEdit : undefined}
					/>
				{/each}

				<!-- Thinking/Streaming message -->
				{#if isStreaming}
					<ChatMessage
						role="assistant"
						content={streamingContent}
						isStreaming={true}
						isThinking={!streamingContent}
					/>
				{/if}

				<!-- Error message -->
				{#if error}
					<div class="max-w-3xl mx-auto px-4 my-4">
						<div class="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
							{error}
						</div>
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Scroll to bottom button -->
	{#if showScrollButton}
		<Button
			variant="outline"
			size="icon"
			class="absolute bottom-32 right-8 size-10 rounded-full shadow-lg z-10"
			onclick={scrollToBottom}
		>
			<ArrowDown class="size-5" />
		</Button>
	{/if}

	<!-- Input (sticky bottom) -->
	<div class="shrink-0 sticky bottom-0 bg-background pb-4 pt-2">
		<ChatInput
			bind:value={inputValue}
			{models}
			bind:selectedModel
			onSubmit={handleSend}
			onStop={handleStop}
			onModelSelect={handleModelSelect}
			loading={isLoading}
			disabled={!selectedModel}
		/>
	</div>
</div>
