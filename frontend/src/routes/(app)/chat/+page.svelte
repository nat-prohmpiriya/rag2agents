<script lang="ts">
	import { goto } from '$app/navigation';
	import LLMChat2 from '$lib/components/llm-chat2/LLMChat2.svelte';
	import { chatStore } from '$lib/stores';

	function handleConversationCreated(id: string) {
		// Reload chat list and navigate to the new conversation
		chatStore.loadInitial();
		goto(`/chat/${id}`);
	}

	function handleNewChat() {
		// Reload chat list when starting fresh
		chatStore.loadInitial();
	}
</script>

<svelte:head>
	<title>New Chat | RAG Agent</title>
</svelte:head>

<LLMChat2
	onConversationCreated={handleConversationCreated}
	onNewChat={handleNewChat}
/>
