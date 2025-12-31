<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { conversationsApi, type ConversationDetail } from '$lib/api/conversations';
	import LLMChat2 from '$lib/components/llm-chat2/LLMChat2.svelte';
	import { chatStore, projectStore } from '$lib/stores';

	// State
	let conversationDetail = $state<ConversationDetail | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Get conversation ID from URL
	let conversationId = $derived($page.params.id);

	// Load data when ID changes
	$effect(() => {
		if (conversationId) {
			loadConversation();
		}
	});

	async function loadConversation() {
		if (!conversationId) return;

		loading = true;
		error = null;

		try {
			conversationDetail = await conversationsApi.get(conversationId);
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

	function handleNewChat() {
		chatStore.loadInitial();
		goto('/chat');
	}

	async function handleDelete() {
		if (!conversationId) return;
		try {
			await conversationsApi.delete(conversationId);
			chatStore.loadInitial();
			goto('/chat');
		} catch (e) {
			console.error('Failed to delete conversation:', e);
		}
	}
</script>

<svelte:head>
	<title>{conversationDetail?.title || 'Chat'} | RAG Agent</title>
</svelte:head>

{#if loading}
	<div class="flex h-full items-center justify-center">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
	</div>
{:else if error}
	<div class="flex h-full flex-col items-center justify-center gap-4 p-8">
		<p class="text-destructive">{error}</p>
		<button
			class="rounded-lg bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
			onclick={() => loadConversation()}
		>
			Retry
		</button>
	</div>
{:else if conversationDetail}
	<LLMChat2
		conversationId={conversationId}
		conversationTitle={conversationDetail.title || 'New conversation'}
		initialMessages={conversationDetail.messages}
		projectId={projectStore.currentProjectId}
		onNewChat={handleNewChat}
		onDelete={handleDelete}
	/>
{/if}
