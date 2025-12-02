<script lang="ts">
	import type { Snippet } from 'svelte';
	import { goto } from '$app/navigation';
	import * as Sheet from '$lib/components/ui/sheet';
	import { Button } from '$lib/components/ui/button';
	import { History } from 'lucide-svelte';
	import ChatHistorySidebar from './ChatHistorySidebar.svelte';
	import type { Conversation } from '$lib/api/conversations';

	let {
		children,
		conversations,
		currentId = null,
		loading = false,
		onDelete
	} = $props<{
		children?: Snippet;
		conversations: Conversation[];
		currentId?: string | null;
		loading?: boolean;
		onDelete: (id: string) => void;
	}>();

	let mobileHistoryOpen = $state(false);

	function handleSelect(id: string) {
		mobileHistoryOpen = false;
		goto(`/chat/${id}`);
	}

	function handleNew() {
		mobileHistoryOpen = false;
		goto('/chat');
	}
</script>

<div class="flex h-[calc(100vh-3.5rem)]">
	<!-- Desktop: Chat history sidebar -->
	<div class="hidden lg:block">
		<ChatHistorySidebar
			{conversations}
			{currentId}
			{loading}
			onSelect={handleSelect}
			onNew={handleNew}
			{onDelete}
		/>
	</div>

	<!-- Mobile: Sheet for history -->
	<div class="lg:hidden">
		<Sheet.Root bind:open={mobileHistoryOpen}>
			<Sheet.Trigger>
				{#snippet child({ props })}
					<Button {...props} variant="ghost" size="icon" class="fixed bottom-20 left-4 z-50 shadow-lg">
						<History class="h-5 w-5" />
					</Button>
				{/snippet}
			</Sheet.Trigger>
			<Sheet.Content side="left" class="w-64 p-0">
				<ChatHistorySidebar
					{conversations}
					{currentId}
					{loading}
					onSelect={handleSelect}
					onNew={handleNew}
					{onDelete}
				/>
			</Sheet.Content>
		</Sheet.Root>
	</div>

	<!-- Main chat area -->
	<div class="flex-1 min-w-0">
		{#if children}
			{@render children()}
		{/if}
	</div>
</div>
