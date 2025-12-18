<script lang="ts">
	import { ChevronDown } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import type { ModelInfo } from '$lib/api/chat';

	interface Props {
		models: ModelInfo[];
		selectedModel: ModelInfo | null;
		onSelect: (model: ModelInfo) => void;
		disabled?: boolean;
	}

	let { models, selectedModel, onSelect, disabled = false }: Props = $props();

	function getProviderIcon(provider: string): string {
		switch (provider.toLowerCase()) {
			case 'openai':
				return '🤖';
			case 'google':
				return '✨';
			case 'anthropic':
				return '🧠';
			default:
				return '🔮';
		}
	}

	function getTierColor(tier?: string): 'default' | 'secondary' | 'destructive' | 'outline' {
		switch (tier) {
			case 'pro':
				return 'default';
			case 'enterprise':
				return 'destructive';
			default:
				return 'secondary';
		}
	}

	// Group models by provider
	let groupedModels = $derived(
		models.reduce(
			(acc, model) => {
				const provider = model.provider;
				if (!acc[provider]) {
					acc[provider] = [];
				}
				acc[provider].push(model);
				return acc;
			},
			{} as Record<string, ModelInfo[]>
		)
	);
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger>
		{#snippet child({ props })}
			<Button
				variant="outline"
				class="min-w-[200px] justify-between gap-2"
				{disabled}
				{...props}
			>
				{#if selectedModel}
					<span class="flex items-center gap-2">
						<span>{getProviderIcon(selectedModel.provider)}</span>
						<span class="font-medium">{selectedModel.name}</span>
						{#if selectedModel.tier === 'pro'}
							<Badge variant="default" class="h-5 px-1.5 text-[10px]">Pro</Badge>
						{/if}
					</span>
				{:else}
					<span class="text-muted-foreground">Select a model</span>
				{/if}
				<ChevronDown class="size-4 opacity-50" />
			</Button>
		{/snippet}
	</DropdownMenu.Trigger>
	<DropdownMenu.Content class="w-[280px]">
		{#each Object.entries(groupedModels) as [provider, providerModels], i}
			{#if i > 0}
				<DropdownMenu.Separator />
			{/if}
			<DropdownMenu.Label
				class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
			>
				<span>{getProviderIcon(provider)}</span>
				<span>{provider}</span>
			</DropdownMenu.Label>
			{#each providerModels as model}
				<DropdownMenu.Item
					class="flex cursor-pointer items-center justify-between gap-2"
					onclick={() => onSelect(model)}
				>
					<div class="flex flex-col gap-0.5">
						<span class="font-medium">{model.name}</span>
						{#if model.description}
							<span class="text-xs text-muted-foreground line-clamp-1"
								>{model.description}</span
							>
						{/if}
					</div>
					{#if model.tier === 'pro'}
						<Badge
							variant={getTierColor(model.tier)}
							class="h-5 shrink-0 px-1.5 text-[10px]"
						>
							Pro
						</Badge>
					{/if}
				</DropdownMenu.Item>
			{/each}
		{/each}
	</DropdownMenu.Content>
</DropdownMenu.Root>
