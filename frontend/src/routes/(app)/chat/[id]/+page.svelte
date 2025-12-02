<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { conversationsApi, type Conversation, type ConversationDetail } from '$lib/api/conversations';
	import { ChatLayout } from '$lib/components/chat';
	import LLMChat from '$lib/components/llm-chat/LLMChat.svelte';

	// State
	let conversations = $state<Conversation[]>([]);
	let conversationDetail = $state<ConversationDetail | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Get conversation ID from URL
	let conversationId = $derived($page.params.id);

	// Load data on mount and when ID changes
	$effect(() => {
		if (conversationId) {
			loadData();
		}
	});

	async function loadData() {
		if (!conversationId) return;

		loading = true;
		error = null;

		try {
			// Load conversations list and detail in parallel
			const [listResponse, detail] = await Promise.all([
				conversationsApi.list(1, 50),
				conversationsApi.get(conversationId)
			]);

			conversations = listResponse.items;
			conversationDetail = detail;
		} catch (e) {
			console.error('Failed to load conversation:', e);
			error = e instanceof Error ? e.message : 'Failed to load conversation';

			// If 404, redirect to new chat
			if (error.includes('404') || error.includes('not found')) {
				goto('/chat');
			}
		} finally {
			loading = false;
		}
	}

	async function handleDelete(id: string) {
		if (!confirm('Delete this conversation?')) return;

		try {
			await conversationsApi.delete(id);
			// Remove from list
			conversations = conversations.filter((c) => c.id !== id);

			// If deleted current conversation, go to new chat
			if (id === conversationId) {
				goto('/chat');
			}
		} catch (e) {
			console.error('Failed to delete conversation:', e);
		}
	}

	function handleNewChat() {
		goto('/chat');
	}

	async function refreshConversations() {
		try {
			const response = await conversationsApi.list(1, 50);
			conversations = response.items;
		} catch (e) {
			console.error('Failed to refresh conversations:', e);
		}
	}
</script>

<svelte:head>
	<title>{conversationDetail?.title || 'Chat'} | RAG Agent</title>
</svelte:head>

<ChatLayout {conversations} currentId={conversationId} {loading} onDelete={handleDelete}>
	{#if loading}
		<div class="flex h-full items-center justify-center">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
		</div>
	{:else if error}
		<div class="flex h-full flex-col items-center justify-center gap-4 p-8">
			<p class="text-destructive">{error}</p>
			<button
				class="rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
				onclick={() => loadData()}
			>
				Retry
			</button>
		</div>
	{:else if conversationDetail}
		<div class="h-full p-4">
			<LLMChat
				conversationId={conversationId}
				initialMessages={conversationDetail.messages}
				onNewChat={handleNewChat}
			/>
		</div>
	{/if}
</ChatLayout>
