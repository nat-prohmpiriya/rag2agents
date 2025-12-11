<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Bot, Plus, Search } from 'lucide-svelte';
	import { agentStore } from '$lib/stores/agents.svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import AgentCard from '$lib/components/agents/AgentCard.svelte';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import type { AgentInfo } from '$lib/api';

	// Delete confirmation
	let deleteDialogOpen = $state(false);
	let agentToDelete = $state<AgentInfo | null>(null);
	let deleting = $state(false);

	// Search
	let searchQuery = $state('');

	// Derived: filter and separate system and user agents
	let filteredAgents = $derived.by(() => {
		if (!searchQuery.trim()) return agentStore.currentAgents;
		const query = searchQuery.toLowerCase();
		return agentStore.currentAgents.filter(
			(a) =>
				a.name.toLowerCase().includes(query) ||
				(a.description?.toLowerCase().includes(query) ?? false)
		);
	});

	let systemAgents = $derived(
		filteredAgents.filter(a => a.source === 'system')
	);
	let userAgents = $derived(
		filteredAgents.filter(a => a.source === 'user')
	);

	onMount(() => {
		agentStore.initFromStorage();
		agentStore.fetchAgents();
	});

	function handleAgentClick(agent: AgentInfo) {
		// Navigate to agent detail page using slug
		goto(`/agents/${agent.slug}`);
	}

	function handleAgentSelect(slug: string) {
		// Select agent and go to chat
		agentStore.selectAgent(slug);
		goto('/chat');
	}

	function openDeleteDialog(agent: AgentInfo) {
		agentToDelete = agent;
		deleteDialogOpen = true;
	}

	async function handleDelete() {
		if (!agentToDelete?.id) return;

		deleting = true;
		try {
			await agentStore.deleteAgent(agentToDelete.id);
			deleteDialogOpen = false;
			agentToDelete = null;
		} catch (e) {
			console.error('Failed to delete agent:', e);
		} finally {
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>Agents | RAG Agent</title>
</svelte:head>

<div class="flex h-full flex-col">
	<!-- Content -->
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-6xl">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center gap-3">
					<Bot class="size-8 text-foreground" />
					<h1 class="text-3xl font-semibold text-foreground">Agents</h1>
				</div>
				<Button onclick={() => goto('/agents/new')}>
					<Plus class="mr-2 size-4" />
					New Agent
				</Button>
			</div>

			<!-- Search -->
			<div class="relative mb-6">
				<Search
					class="absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted-foreground"
				/>
				<Input
					type="search"
					placeholder="Search agents..."
					class="pl-12 h-12 bg-white border-border rounded-lg text-base"
					bind:value={searchQuery}
				/>
			</div>

			<div class="space-y-8">
			{#if agentStore.loading}
				<div class="flex items-center justify-center py-12">
					<div
						class="size-8 animate-spin rounded-full border-4 border-muted border-t-primary"
					></div>
				</div>
			{:else if agentStore.currentError}
				<div class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center">
					<p class="text-destructive">{agentStore.currentError}</p>
				</div>
			{:else if filteredAgents.length === 0}
				<div class="rounded-lg bg-white border border-border flex flex-col items-center p-12">
					<Bot class="size-12 text-muted-foreground/50" />
					<h3 class="mt-4 text-lg font-medium">
						{#if searchQuery}
							No agents found
						{:else}
							No agents available
						{/if}
					</h3>
					<p class="mt-1 text-sm text-muted-foreground">
						{#if searchQuery}
							No agents matching "{searchQuery}". Try a different search.
						{:else}
							Create your first agent to get started.
						{/if}
					</p>
					{#if !searchQuery}
						<Button class="mt-4" onclick={() => goto('/agents/new')}>
							<Plus class="mr-2 size-4" />
							Create Agent
						</Button>
					{/if}
				</div>
			{:else}
				<!-- My Agents Section -->
				{#if userAgents.length > 0}
					<section>
						<h2 class="text-sm font-medium text-muted-foreground mb-4">My Agents</h2>
						<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
							{#each userAgents as agent (agent.slug)}
								<AgentCard
									{agent}
									selected={agentStore.currentSelectedSlug === agent.slug}
									onclick={() => handleAgentClick(agent)}
									onEdit={() => handleAgentClick(agent)}
									onDelete={() => openDeleteDialog(agent)}
								/>
							{/each}
						</div>
					</section>
				{/if}

				<!-- System Agents Section -->
				{#if systemAgents.length > 0}
					<section>
						<h2 class="text-sm font-medium text-muted-foreground mb-4">System Agents</h2>
						<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
							{#each systemAgents as agent (agent.slug)}
								<AgentCard
									{agent}
									selected={agentStore.currentSelectedSlug === agent.slug}
									onclick={() => handleAgentClick(agent)}
								/>
							{/each}
						</div>
					</section>
				{/if}
			{/if}
			</div>
		</div>
	</div>
</div>

<!-- Delete Confirmation Dialog -->
<AlertDialog.Root bind:open={deleteDialogOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete Agent</AlertDialog.Title>
			<AlertDialog.Description>
				Are you sure you want to delete "{agentToDelete?.name}"? This action cannot be undone.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={deleting}>Cancel</AlertDialog.Cancel>
			<AlertDialog.Action
				class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
				disabled={deleting}
				onclick={handleDelete}
			>
				{deleting ? 'Deleting...' : 'Delete'}
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
