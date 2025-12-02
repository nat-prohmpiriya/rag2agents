<script lang="ts">
	import { onMount } from 'svelte';
	import { chatApi, type ModelInfo } from '$lib/api/chat';
	import * as ScrollArea from '$lib/components/ui/scroll-area';
	import ChatHeader from './ChatHeader.svelte';
	import ChatInput from './ChatInput.svelte';
	import ChatMessage from './ChatMessage.svelte';
	import type { ModelConfigValues } from './ModelConfig.svelte';
	import type { Message as ApiMessage } from '$lib/api/conversations';

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
		createdAt: Date;
	}

	interface Props {
		conversationId?: string;
		initialMessages?: ApiMessage[];
		initialModel?: string;
		onConversationCreated?: (id: string) => void;
		onNewChat?: () => void;
	}

	let {
		conversationId = $bindable(),
		initialMessages = [],
		initialModel,
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
			syncStatus = 'syncing';
			const response = await chatApi.getModels();
			models = response.models;

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
					stream: true
				},
				(content) => {
					streamingContent += content;
					scrollToBottom();
				},
				(newConversationId) => {
					// On done - add assistant message
					const assistantMessage: Message = {
						id: crypto.randomUUID(),
						role: 'assistant',
						content: streamingContent,
						createdAt: new Date()
					};
					messages = [...messages, assistantMessage];
					streamingContent = '';
					isStreaming = false;
					isLoading = false;

					// If this was a new conversation, notify parent
					if (newConversationId && !conversationId) {
						conversationId = newConversationId;
						onConversationCreated?.(newConversationId);
					}
				},
				(errorMsg) => {
					error = errorMsg;
					isStreaming = false;
					isLoading = false;
				}
			);
		} catch (e) {
			console.error('Chat error:', e);
			error = e instanceof Error ? e.message : 'Failed to send message';
			isStreaming = false;
			isLoading = false;
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

	function scrollToBottom() {
		setTimeout(() => {
			messagesEndRef?.scrollIntoView({ behavior: 'smooth' });
		}, 100);
	}
</script>

<div class="flex h-full flex-col bg-background border rounded-xl shadow-md">
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
	/>

	<!-- Messages Area -->
	<ScrollArea.Root class="flex-1">
		<div class="flex flex-col">
			{#if messages.length === 0}
				<!-- Empty state -->
				<div class="flex flex-1 items-center justify-center p-8 text-muted-foreground">
					<p>Start a conversation by typing a message below.</p>
				</div>
			{:else}
				<!-- Messages -->
				{#each messages as message (message.id)}
					<ChatMessage role={message.role} content={message.content} />
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
	<ChatInput bind:value={inputValue} onSend={handleSend} loading={isLoading} disabled={!selectedModel} />
</div>
