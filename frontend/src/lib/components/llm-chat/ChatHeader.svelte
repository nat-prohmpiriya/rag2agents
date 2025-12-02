<script lang="ts">
	import {
		RefreshCw,
		Copy,
		SlidersHorizontal,
		Plus,
		MoreHorizontal,
		Check
	} from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Popover from '$lib/components/ui/popover';
	import ModelSelector from './ModelSelector.svelte';
	import ModelConfig, { type ModelConfigValues } from './ModelConfig.svelte';
	import type { ModelInfo } from '$lib/api/chat';

	interface Props {
		models: ModelInfo[];
		selectedModel: ModelInfo | null;
		onModelSelect: (model: ModelInfo) => void;
		syncStatus?: 'synced' | 'syncing' | 'error';
		onNewChat?: () => void;
		onRefresh?: () => void;
		onCopy?: () => void;
		onConfigChange?: (config: ModelConfigValues) => void;
		configValues?: ModelConfigValues;
		disabled?: boolean;
	}

	let {
		models,
		selectedModel,
		onModelSelect,
		syncStatus = 'synced',
		onNewChat,
		onRefresh,
		onCopy,
		onConfigChange,
		configValues,
		disabled = false
	}: Props = $props();

	let copied = $state(false);

	function handleCopy() {
		if (onCopy) {
			onCopy();
			copied = true;
			setTimeout(() => {
				copied = false;
			}, 2000);
		}
	}

	function getSyncStatusText(status: string): string {
		switch (status) {
			case 'synced':
				return 'Synced';
			case 'syncing':
				return 'Syncing...';
			case 'error':
				return 'Sync Error';
			default:
				return 'Unknown';
		}
	}
</script>

<header class="flex items-center justify-between border-b px-4 py-2 bg-gray-50 rounded-t-xl">
	<div class="flex items-center gap-3">
		<ModelSelector {models} {selectedModel} onSelect={onModelSelect} {disabled} />
	</div>

	<div class="flex items-center gap-2">
		<!-- Sync Status -->
		<!-- <Badge variant="outline" class="gap-1.5">
			{#if syncStatus === 'syncing'}
				<RefreshCw class="size-3 animate-spin" />
			{:else if syncStatus === 'synced'}
				<Check class="size-3 text-green-500" />
			{:else}
				<span class="size-2 rounded-full bg-red-500"></span>
			{/if}
			<span class="text-xs">{getSyncStatusText(syncStatus)}</span>
		</Badge> -->

		<!-- Action Buttons -->
		<!-- <Button variant="ghost" size="icon-sm" onclick={onRefresh} {disabled} title="Refresh">
			<RefreshCw class="size-4" />
		</Button>

		<Button
			variant="ghost"
			size="icon-sm"
			onclick={handleCopy}
			{disabled}
			title="Copy conversation"
		>
			{#if copied}
				<Check class="size-4 text-green-500" />
			{:else}
				<Copy class="size-4" />
			{/if}
		</Button> -->

		<!-- Settings Popover -->
		<Popover.Root>
			<Popover.Trigger>
				{#snippet child({ props })}
					<Button
						variant="ghost"
						size="icon-sm"
						{disabled}
						title="Settings"
						class="cursor-pointer"
						{...props}
					>
						<SlidersHorizontal class="size-4" />
					</Button>
				{/snippet}
			</Popover.Trigger>
			<Popover.Content align="end" class="w-auto p-0">
				<ModelConfig values={configValues} onChange={onConfigChange} />
			</Popover.Content>
		</Popover.Root>

		<Button variant="ghost" size="icon-sm" onclick={onNewChat} {disabled} title="New chat">
			<Plus class="size-4" />
		</Button>

		<!-- More Menu -->
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Button variant="ghost" size="icon-sm" {...props}>
						<MoreHorizontal class="size-4" />
					</Button>
				{/snippet}
			</DropdownMenu.Trigger>
			<DropdownMenu.Content align="end">
				<DropdownMenu.Item onclick={onNewChat}>
					<Plus class="mr-2 size-4" />
					New Chat
				</DropdownMenu.Item>
				<DropdownMenu.Item onclick={handleCopy}>
					<Copy class="mr-2 size-4" />
					Copy Conversation
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</div>
</header>
