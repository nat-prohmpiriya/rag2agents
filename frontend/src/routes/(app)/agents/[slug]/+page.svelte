<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { Loader2 } from 'lucide-svelte';
	import LLMChat2 from '$lib/components/llm-chat2/LLMChat2.svelte';
	import { chatStore } from '$lib/stores';
	import { agentsApi } from '$lib/api';
	import type { AgentDetail } from '$lib/api';

	// Get agent slug from URL
	let agentSlug = $derived($page.params.slug);

	// Agent data
	let agent = $state<AgentDetail | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(async () => {
		await loadAgent();
	});

	async function loadAgent() {
		if (!agentSlug) {
			error = 'Agent slug is required';
			loading = false;
			return;
		}

		loading = true;
		error = null;
		try {
			agent = await agentsApi.get(agentSlug);
		} catch (e) {
			console.error('Failed to load agent:', e);
			error = e instanceof Error ? e.message : 'Failed to load agent';
		} finally {
			loading = false;
		}
	}

	function handleConversationCreated(id: string) {
		// Reload chat list and navigate to the conversation
		chatStore.loadInitial();
		goto(`/chat/${id}`);
	}

	function handleNewChat() {
		chatStore.loadInitial();
	}
</script>

<svelte:head>
	<title>{agent?.name || 'Agent'} | RAG Agent</title>
</svelte:head>

{#if loading}
	<div class="flex h-full items-center justify-center">
		<Loader2 class="size-8 animate-spin text-muted-foreground" />
	</div>
{:else if error}
	<div class="flex h-full items-center justify-center">
		<div class="text-center">
			<p class="text-destructive mb-4">{error}</p>
			<button
				class="text-primary hover:underline"
				onclick={() => goto('/agents')}
			>
				Back to Agents
			</button>
		</div>
	</div>
{:else if agent}
	<LLMChat2
		agentSlug={agent.slug}
		conversationTitle={agent.name}
		onConversationCreated={handleConversationCreated}
		onNewChat={handleNewChat}
	/>
{/if}
