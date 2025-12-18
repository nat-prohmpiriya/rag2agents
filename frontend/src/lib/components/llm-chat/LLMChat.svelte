<script lang="ts">
	import { onMount } from 'svelte';
	import { chatApi, type ModelInfo, type SourceInfo } from '$lib/api/chat';
	import { documentsApi } from '$lib/api/documents';
	import * as ScrollArea from '$lib/components/ui/scroll-area';
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ChatMessage from './ChatMessage.svelte';
	import type { ModelConfigValues } from './ModelConfig.svelte';
	import type { Message as ApiMessage } from '$lib/api/conversations';
	import { agentStore } from '$lib/stores/agents.svelte';

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		createdAt: Date;
		sources?: SourceInfo[];
	}

	interface Props {
		conversationId?: string;
		initialMessages?: ApiMessage[];
		initialModel?: string;
		projectId?: string;
		projectName?: string;
		onConversationCreated?: (id: string) => void;
		onNewChat?: () => void;
	}

	let {
		conversationId = $bindable(),
		initialMessages = [],
		initialModel,
		projectId,
		projectName,
		onConversationCreated,
		onNewChat
	}: Props = $props();

	// State
	let models = $state<ModelInfo[]>([]);
	let selectedModel = $state<ModelInfo | null>(null);
	let messages = $state<Message[]>([]);
	let inputValue = $state('');
	let isLoading = $state(false);
	let isStreaming = $state(false);
	let streamingContent = $state('');
	let syncStatus = $state<'synced' | 'syncing' | 'error'>('synced');
	let error = $state<string | null>(null);
	let messagesEndRef = $state<HTMLDivElement | null>(null);

	// Model config state
	let modelConfig = $state<ModelConfigValues>({
		maxOutputTokens: 64000,
		temperature: 0.7,
		topP: 1,
		frequencyPenalty: 0,
		presencePenalty: 0
	});

	// RAG state
	let useRag = $state(false);
	let hasReadyDocuments = $state(false);

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

	// Load models and check documents on mount
	onMount(async () => {
		await Promise.all([loadModels(), checkReadyDocuments()]);
	});

	async function checkReadyDocuments() {
		try {
			const response = await documentsApi.list(1, 100);
			hasReadyDocuments = response.items.some((doc) => doc.status === 'ready');
		} catch (e) {
			console.error('Failed to check documents:', e);
			hasReadyDocuments = false;
		}
	}

	async function loadModels() {
		try {
			syncStatus = 'syncing';
			const response = await chatApi.getModels();
			// Filter out image generation and embedding models
			models = response.models.filter((m: ModelInfo) =>
				!m.id.toLowerCase().includes('imagen') &&
				!m.id.toLowerCase().includes('embedding')
			);

			// Select initial model or first available
			if (initialModel) {
				selectedModel = models.find((m) => m.id === initialModel) || models[0] || null;
			} else {
				selectedModel = models[0] || null;
			}

			syncStatus = 'synced';
		} catch (e) {
			console.error('Failed to load models:', e);
			syncStatus = 'error';
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
					temperature: modelConfig.temperature,
					max_tokens: modelConfig.maxOutputTokens,
					top_p: modelConfig.topP,
					frequency_penalty: modelConfig.frequencyPenalty,
					presence_penalty: modelConfig.presencePenalty,
					stream: true,
					use_rag: useRag && hasReadyDocuments,
					rag_top_k: 5,
					project_id: projectId,
					agent_slug: agentStore.currentSelectedSlug || undefined
				},
				(content) => {
					streamingContent += content;
					scrollToBottom();
				},
				(doneData) => {
					// On done - add assistant message with sources
					const assistantMessage: Message = {
						id: crypto.randomUUID(),
						role: 'assistant',
						content: streamingContent,
						createdAt: new Date(),
						sources: doneData.sources
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

	function handleNewChatClick() {
		messages = [];
		streamingContent = '';
		error = null;
		conversationId = undefined;
		onNewChat?.();
	}

	function handleRefresh() {
		loadModels();
	}

	function handleCopy() {
		const text = messages
			.map((m) => `${m.role === 'user' ? 'You' : 'Assistant'}: ${m.content}`)
			.join('\n\n');
		navigator.clipboard.writeText(text);
	}

	function handleConfigChange(config: ModelConfigValues) {
		modelConfig = config;
	}

	function handleUseRagChange(value: boolean) {
		useRag = value;
	}

	// Throttled scroll to avoid too many scroll calls during streaming
	let scrollTimeout: ReturnType<typeof setTimeout> | null = null;
	function scrollToBottom() {
		if (scrollTimeout) return; // Already scheduled
		scrollTimeout = setTimeout(() => {
			messagesEndRef?.scrollIntoView({ behavior: 'smooth' });
			scrollTimeout = null;
		}, 50);
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
					temperature: modelConfig.temperature,
					max_tokens: modelConfig.maxOutputTokens,
					top_p: modelConfig.topP,
					frequency_penalty: modelConfig.frequencyPenalty,
					presence_penalty: modelConfig.presencePenalty,
					stream: true,
					use_rag: useRag && hasReadyDocuments,
					rag_top_k: 5,
					project_id: projectId,
					agent_slug: agentStore.currentSelectedSlug || undefined,
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
						sources: doneData.sources
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

	// Check if message is the last assistant message
	function isLastAssistantMessage(index: number): boolean {
		if (messages[index].role !== 'assistant') return false;
		// Check if there are any assistant messages after this one
		for (let i = index + 1; i < messages.length; i++) {
			if (messages[i].role === 'assistant') return false;
		}
		return true;
	}

	// Check if message is the last user message
	function isLastUserMessage(index: number): boolean {
		if (messages[index].role !== 'user') return false;
		// Check if there are any user messages after this one
		for (let i = index + 1; i < messages.length; i++) {
			if (messages[i].role === 'user') return false;
		}
		return true;
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
</script>

<div class="flex h-full flex-col bg-background border rounded-xl shadow-md overflow-hidden min-w-0">
	<!-- Header -->
	<ChatHeader
		{models}
		{selectedModel}
		onModelSelect={handleModelSelect}
		{syncStatus}
		onNewChat={handleNewChatClick}
		onRefresh={handleRefresh}
		onCopy={handleCopy}
		onConfigChange={handleConfigChange}
		configValues={modelConfig}
		disabled={isLoading}
		{useRag}
		onUseRagChange={handleUseRagChange}
		{hasReadyDocuments}
		{projectName}
	/>

	<!-- Messages Area -->
	<ScrollArea.Root class="flex-1 min-h-0">
		<div class="flex flex-col min-w-0">
			{#if messages.length === 0}
				<!-- Empty state -->
				<div class="flex flex-1 items-center justify-center p-8 text-muted-foreground">
					<p>Start a conversation by typing a message below.</p>
				</div>
			{:else}
				<!-- Messages -->
				{#each messages as message, index (message.id)}
					<ChatMessage
						role={message.role}
						content={message.content}
						sources={message.sources}
						createdAt={message.createdAt}
						isLastAssistant={isLastAssistantMessage(index)}
						isLastUser={isLastUserMessage(index)}
						onRegenerate={isLastAssistantMessage(index) ? handleRegenerate : undefined}
						onEdit={isLastUserMessage(index) ? handleEdit : undefined}
					/>
				{/each}

				<!-- Streaming message -->
				{#if isStreaming && streamingContent}
					<ChatMessage role="assistant" content={streamingContent} isStreaming={true} />
				{/if}

				<!-- Error message -->
				{#if error}
					<div class="mx-4 my-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
						{error}
					</div>
				{/if}

				<div bind:this={messagesEndRef}></div>
			{/if}
		</div>
	</ScrollArea.Root>

	<!-- Input -->
	<ChatInput bind:value={inputValue} onSend={handleSend} onStop={handleStop} loading={isLoading} disabled={!selectedModel} />
</div>
