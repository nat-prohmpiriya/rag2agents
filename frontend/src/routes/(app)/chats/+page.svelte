<script lang="ts">
	import { MessageSquare, Search, Trash2, Plus, X, MoreHorizontal, Archive } from 'lucide-svelte';
	import { Input } from '$lib/components/ui/input';
	import { Button } from '$lib/components/ui/button';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { conversationsApi, type Conversation } from '$lib/api';
	import { chatStore } from '$lib/stores';
	import * as m from '$lib/paraglide/messages';

	let conversations = $state<Conversation[]>([]);
	let loading = $state(true);
	let searchQuery = $state('');

	// Selection state
	let selectMode = $state(false);
	let selectedIds = $state<Set<string>>(new Set());
	let hoveredId = $state<string | null>(null);

	let filteredConversations = $derived(
		searchQuery
			? conversations.filter((c) =>
					(c.title ?? '').toLowerCase().includes(searchQuery.toLowerCase()) ||
					(c.last_message_preview ?? '').toLowerCase().includes(searchQuery.toLowerCase())
				)
			: conversations
	);

	let selectedCount = $derived(selectedIds.size);
	let allSelected = $derived(
		filteredConversations.length > 0 && selectedIds.size === filteredConversations.length
	);

	onMount(async () => {
		await loadConversations();
	});

	async function loadConversations() {
		try {
			const response = await conversationsApi.list(1, 100);
			conversations = response.items;
		} catch (e) {
			console.error('Failed to load conversations:', e);
		} finally {
			loading = false;
		}
	}

	function toggleSelectMode() {
		selectMode = !selectMode;
		if (!selectMode) {
			selectedIds = new Set();
		}
	}

	function toggleSelect(id: string, e?: MouseEvent) {
		e?.stopPropagation();
		const newSet = new Set(selectedIds);
		if (newSet.has(id)) {
			newSet.delete(id);
		} else {
			newSet.add(id);
		}
		selectedIds = newSet;

		// Enter select mode if selecting
		if (newSet.size > 0 && !selectMode) {
			selectMode = true;
		}
	}

	function toggleSelectAll() {
		if (allSelected) {
			selectedIds = new Set();
		} else {
			selectedIds = new Set(filteredConversations.map((c) => c.id));
		}
	}

	async function handleDelete(id: string, e?: MouseEvent) {
		e?.stopPropagation();
		try {
			await conversationsApi.delete(id);
			conversations = conversations.filter((c) => c.id !== id);
			selectedIds.delete(id);
			selectedIds = new Set(selectedIds);
			// Refresh sidebar chat list
			chatStore.loadInitial();
		} catch (e) {
			console.error('Failed to delete conversation:', e);
		}
	}

	async function handleDeleteSelected() {
		const idsToDelete = Array.from(selectedIds);
		try {
			await Promise.all(idsToDelete.map((id) => conversationsApi.delete(id)));
			conversations = conversations.filter((c) => !selectedIds.has(c.id));
			selectedIds = new Set();
			selectMode = false;
			// Refresh sidebar chat list
			chatStore.loadInitial();
		} catch (e) {
			console.error('Failed to delete conversations:', e);
		}
	}

	function handleClick(id: string) {
		if (selectMode) {
			toggleSelect(id);
		} else {
			goto(`/chat/${id}`);
		}
	}

	function formatTimeAgo(dateString: string): string {
		const date = new Date(dateString);
		const now = new Date();
		const diff = now.getTime() - date.getTime();

		const minutes = Math.floor(diff / (1000 * 60));
		const hours = Math.floor(diff / (1000 * 60 * 60));
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));

		if (minutes < 1) return m.time_just_now();
		if (minutes === 1) return m.time_minute_ago({ count: minutes });
		if (minutes < 60) return m.time_minutes_ago({ count: minutes });
		if (hours === 1) return m.time_hour_ago({ count: hours });
		if (hours < 24) return m.time_hours_ago({ count: hours });
		if (days === 1) return m.time_day_ago();
		if (days < 7) return m.time_days_ago({ count: days });
		return date.toLocaleDateString();
	}

	function getDisplayTitle(conv: Conversation): string {
		if (conv.title) return conv.title;
		if (conv.last_message_preview) {
			return conv.last_message_preview.length > 50
				? conv.last_message_preview.substring(0, 50) + '...'
				: conv.last_message_preview;
		}
		return m.sidebar_new_conversation();
	}
</script>

<svelte:head>
	<title>{m.chats_page_title()}</title>
</svelte:head>

<div class="flex h-full flex-col">
	<!-- Content -->
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-6xl">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center gap-3">
					<MessageSquare class="size-8 text-foreground" />
					<h1 class="text-3xl font-semibold text-foreground">{m.chats_title()}</h1>
				</div>
				<Button href="/chat">
					<Plus class="mr-2 size-4" />
					{m.chats_new_chat()}
				</Button>
			</div>

			<!-- Search -->
			<div class="relative mb-6">
				<Search
					class="absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted-foreground"
				/>
				<Input
					type="search"
					placeholder={m.chats_search_placeholder()}
					class="pl-12 h-12 bg-white border-border rounded-lg text-base"
					bind:value={searchQuery}
				/>
			</div>

			<!-- Stats & Select toggle -->
			<div class="flex items-center justify-between mb-4">
				<span class="text-sm text-muted-foreground">
					{conversations.length} {conversations.length === 1 ? 'chat' : 'chats'}
				</span>
				{#if !selectMode}
					<Button variant="link" class="text-sm p-0 h-auto" onclick={toggleSelectMode}>
						{m.common_select()}
					</Button>
				{/if}
			</div>

			<div class="bg-white rounded-lg border border-border">
			<!-- Selection toolbar -->
			{#if selectMode}
				<div class="flex items-center gap-3 px-6 py-3 bg-muted/50">
					<div class="w-5 flex justify-center">
						<Checkbox checked={allSelected} onCheckedChange={toggleSelectAll} />
					</div>
					<span class="text-sm font-medium">{m.common_selected({ count: selectedCount })}</span>

					<div class="flex items-center gap-1">
						<Button
							variant="ghost"
							size="icon"
							disabled={selectedCount === 0}
							onclick={handleDeleteSelected}
							title={m.chats_delete_selected()}
						>
							<Trash2 class="size-4" />
						</Button>
					</div>

					<div class="flex-1"></div>

					<Button variant="ghost" size="icon" onclick={toggleSelectMode}>
						<X class="size-4" />
					</Button>
				</div>
			{/if}
			{#if loading}
				<div class="flex items-center justify-center py-12">
					<div
						class="size-8 animate-spin rounded-full border-4 border-muted border-t-primary"
					></div>
				</div>
			{:else if filteredConversations.length === 0}
				<div class="flex flex-col items-center p-12 text-center rounded-lg">
					<MessageSquare class="size-12 text-muted-foreground/50" />
					<h3 class="mt-4 text-lg font-medium">{m.chats_no_conversations()}</h3>
					<p class="mt-1 text-sm text-muted-foreground">
						{#if searchQuery}
							{m.chats_no_match({ query: searchQuery })}
						{:else}
							{m.chats_empty_hint()}
						{/if}
					</p>
					<Button class="mt-4" href="/chat">
						<Plus class="mr-2 size-4" />
						{m.chats_new_chat()}
					</Button>
				</div>
			{:else}
				<div class="divide-y">
					{#each filteredConversations as conversation (conversation.id)}
						{@const isSelected = selectedIds.has(conversation.id)}
						{@const isHovered = hoveredId === conversation.id}
						<div
							class="flex items-center gap-3 px-6 py-4 cursor-pointer transition-colors hover:bg-accent/50 {isSelected
								? 'bg-accent'
								: ''}"
							onclick={() => handleClick(conversation.id)}
							onmouseenter={() => (hoveredId = conversation.id)}
							onmouseleave={() => (hoveredId = null)}
							role="button"
							tabindex="0"
							onkeydown={(e) => e.key === 'Enter' && handleClick(conversation.id)}
						>
							<!-- Checkbox (show on hover or select mode) -->
							<div
								class="w-5 flex justify-center {selectMode || isHovered
									? 'opacity-100'
									: 'opacity-0'}"
							>
								<Checkbox
									checked={isSelected}
									onCheckedChange={() => toggleSelect(conversation.id)}
									onclick={(e) => e.stopPropagation()}
								/>
							</div>

							<!-- Content -->
							<div class="flex-1 min-w-0">
								<h3 class="font-medium truncate">
									{getDisplayTitle(conversation)}
								</h3>
								<p class="text-xs font-light text-muted-foreground">
									{m.chats_last_message({ time: formatTimeAgo(conversation.updated_at) })}
								</p>
							</div>

							<!-- 3-dot menu (show on hover, not in select mode) -->
							{#if isHovered && !selectMode}
								<DropdownMenu.Root>
									<DropdownMenu.Trigger>
										{#snippet child({ props })}
											<Button
												{...props}
												variant="ghost"
												size="icon"
												class="size-8"
												onclick={(e) => e.stopPropagation()}
											>
												<MoreHorizontal class="size-4" />
											</Button>
										{/snippet}
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="end">
										<DropdownMenu.Item
											class="text-destructive focus:text-destructive"
											onclick={(e) => handleDelete(conversation.id, e)}
										>
											<Trash2 class="mr-2 size-4" />
											{m.common_delete()}
										</DropdownMenu.Item>
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
			</div>
		</div>
	</div>
</div>
