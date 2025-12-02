<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { conversationsApi, type Conversation } from '$lib/api/conversations';
	import { ChatLayout } from '$lib/components/chat';
	import LLMChat from '$lib/components/llm-chat/LLMChat.svelte';

	// State
	let conversations = $state<Conversation[]>([]);
	let loading = $state(true);

	onMount(async () => {
		await loadConversations();
	});

	async function loadConversations() {
		loading = true;
		try {
			const response = await conversationsApi.list(1, 50);
			conversations = response.items;
		} catch (e) {
			console.error('Failed to load conversations:', e);
		} finally {
			loading = false;
		}
	}

	async function handleDelete(id: string) {
		if (!confirm('Delete this conversation?')) return;

		try {
			await conversationsApi.delete(id);
			conversations = conversations.filter((c) => c.id !== id);
		} catch (e) {
			console.error('Failed to delete conversation:', e);
		}
	}

	function handleConversationCreated(id: string) {
		// Navigate to the new conversation
		goto(`/chat/${id}`);
	}

	async function handleNewChat() {
		// Reload conversations when starting fresh
		await loadConversations();
	}
</script>

<svelte:head>
	<title>New Chat | RAG Agent</title>
</svelte:head>

<ChatLayout {conversations} currentId={null} {loading} onDelete={handleDelete}>
	<div class="h-full p-4">
		<LLMChat onConversationCreated={handleConversationCreated} onNewChat={handleNewChat} />
	</div>
</ChatLayout>
