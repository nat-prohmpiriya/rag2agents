<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { Plus, ArrowUp, Square, ChevronDown, SlidersHorizontal, History } from 'lucide-svelte';
	import type { ModelInfo } from '$lib/api/chat';

	let {
		value = $bindable(''),
		placeholder = 'Reply...',
		disabled = false,
		loading = false,
		models = [],
		selectedModel = $bindable<ModelInfo | null>(null),
		onSubmit,
		onStop,
		onAttach,
		onModelSelect
	} = $props<{
		value?: string;
		placeholder?: string;
		disabled?: boolean;
		loading?: boolean;
		models?: ModelInfo[];
		selectedModel?: ModelInfo | null;
		onSubmit?: (message: string) => void;
		onStop?: () => void;
		onAttach?: () => void;
		onModelSelect?: (model: ModelInfo) => void;
	}>();

	let textareaRef: HTMLTextAreaElement;

	function handleSubmit() {
		if (!value.trim() || disabled || loading) return;
		onSubmit?.(value.trim());
		value = '';
		// Reset height
		if (textareaRef) {
			textareaRef.style.height = 'auto';
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit();
		}
	}

	function handleInput() {
		// Auto-resize textarea
		if (textareaRef) {
			textareaRef.style.height = 'auto';
			textareaRef.style.height = Math.min(textareaRef.scrollHeight, 200) + 'px';
		}
	}

	function getProviderIcon(provider: string): string {
		switch (provider.toLowerCase()) {
			case 'openai':
				return '🤖';
			case 'google':
				return '✨';
			case 'anthropic':
				return '🧠';
			case 'groq':
				return '⚡';
			default:
				return '🔮';
		}
	}

	// Group models by provider
	let groupedModels = $derived.by(() => {
		const result: Record<string, ModelInfo[]> = {};
		for (const model of models) {
			const provider = model.provider;
			if (!result[provider]) {
				result[provider] = [];
			}
			result[provider].push(model);
		}
		return result;
	});

	let canSubmit = $derived(value.trim().length > 0 && !disabled && !loading);
</script>

<div class="w-full max-w-3xl mx-auto px-4">
	<div class="rounded-3xl border bg-muted/30 shadow-sm overflow-hidden">
		<!-- Textarea area (top) -->
		<div class="px-4 pt-4 pb-2">
			<textarea
				bind:this={textareaRef}
				bind:value
				{placeholder}
				{disabled}
				rows={1}
				class="w-full resize-none bg-transparent text-base placeholder:text-muted-foreground focus:outline-none disabled:cursor-not-allowed disabled:opacity-50 max-h-[200px]"
				onkeydown={handleKeydown}
				oninput={handleInput}
			></textarea>
		</div>

		<!-- Bottom toolbar -->
		<div class="flex items-center justify-between px-2 pb-2">
			<!-- Left side buttons -->
			<div class="flex items-center">
				<!-- Attachment button -->
				<Button
					variant="ghost"
					size="icon"
					class="size-10 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted"
					onclick={onAttach}
					{disabled}
				>
					<Plus class="size-5" />
				</Button>
				<!-- Settings button -->
				<Button
					variant="ghost"
					size="icon"
					class="size-10 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted"
				>
					<SlidersHorizontal class="size-5" />
				</Button>
				<!-- History button -->
				<Button
					variant="ghost"
					size="icon"
					class="size-10 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted"
				>
					<History class="size-5" />
				</Button>
			</div>

			<!-- Right side: Model selector + Send button -->
			<div class="flex items-center gap-2">
				<!-- Model selector -->
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Button
								variant="ghost"
								class="h-9 gap-1.5 text-sm font-medium rounded-xl"
								{...props}
							>
								{#if selectedModel}
									<span>{selectedModel.name}</span>
								{:else}
									<span>Select model</span>
								{/if}
								<ChevronDown class="size-4 text-muted-foreground" />
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end" class="w-[280px]">
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
									onclick={() => onModelSelect?.(model)}
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
											variant="default"
											class="h-5 shrink-0 px-1.5 text-[10px]">Pro</Badge
										>
									{/if}
								</DropdownMenu.Item>
							{/each}
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>

				<!-- Submit/Stop button with loading spinner -->
				<div class="relative">
					{#if loading}
						<!-- Loading spinner ring around button -->
						<div class="absolute inset-0 -m-1">
							<svg class="size-12 animate-spin" viewBox="0 0 48 48">
								<circle
									cx="24"
									cy="24"
									r="20"
									fill="none"
									stroke="currentColor"
									stroke-width="3"
									stroke-linecap="round"
									stroke-dasharray="80 40"
									class="text-primary"
								/>
							</svg>
						</div>
						<Button
							size="icon"
							class="size-10 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
							onclick={onStop}
						>
							<Square class="size-4" />
						</Button>
					{:else}
						<Button
							size="icon"
							class="size-10 rounded-xl {canSubmit
								? 'bg-primary text-primary-foreground hover:bg-primary/90'
								: 'bg-muted text-muted-foreground'}"
							onclick={handleSubmit}
							disabled={!canSubmit}
						>
							<ArrowUp class="size-5" />
						</Button>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>
