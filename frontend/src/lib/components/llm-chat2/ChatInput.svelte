<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import { ImagePlus, ArrowUp, Square, ChevronDown, Brain, X, Wrench, Globe, Check } from 'lucide-svelte';
	import type { ModelInfo } from '$lib/api/chat';

	interface UploadedImage {
		id: string;
		file: File;
		preview: string;
	}

	let {
		value = $bindable(''),
		placeholder = 'Reply...',
		disabled = false,
		loading = false,
		models = [],
		selectedModel = $bindable<ModelInfo | null>(null),
		thinkingEnabled = $bindable(false),
		webSearchEnabled = $bindable(false),
		images = $bindable<UploadedImage[]>([]),
		onSubmit,
		onStop,
		onModelSelect
	} = $props<{
		value?: string;
		placeholder?: string;
		disabled?: boolean;
		loading?: boolean;
		models?: ModelInfo[];
		selectedModel?: ModelInfo | null;
		thinkingEnabled?: boolean;
		webSearchEnabled?: boolean;
		images?: UploadedImage[];
		onSubmit?: (message: string, images?: UploadedImage[]) => void;
		onStop?: () => void;
		onModelSelect?: (model: ModelInfo) => void;
	}>();

	let fileInputRef: HTMLInputElement;

	let textareaRef: HTMLTextAreaElement;

	function handleSubmit() {
		if ((!value.trim() && images.length === 0) || disabled || loading) return;
		onSubmit?.(value.trim(), images.length > 0 ? images : undefined);
		value = '';
		images = [];
		// Reset height
		if (textareaRef) {
			textareaRef.style.height = 'auto';
		}
	}

	function handleImageSelect() {
		fileInputRef?.click();
	}

	function handleFileChange(e: Event) {
		const input = e.target as HTMLInputElement;
		const files = input.files;
		if (!files) return;

		for (const file of files) {
			if (file.type.startsWith('image/')) {
				const reader = new FileReader();
				reader.onload = () => {
					const newImage: UploadedImage = {
						id: crypto.randomUUID(),
						file,
						preview: reader.result as string
					};
					images = [...images, newImage];
				};
				reader.readAsDataURL(file);
			}
		}
		// Reset input
		input.value = '';
	}

	function removeImage(id: string) {
		images = images.filter(img => img.id !== id);
	}

	function toggleThinking() {
		thinkingEnabled = !thinkingEnabled;
	}

	function toggleWebSearch() {
		webSearchEnabled = !webSearchEnabled;
	}

	// Count active tools for badge
	let activeToolsCount = $derived((webSearchEnabled ? 1 : 0));

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

	let canSubmit = $derived((value.trim().length > 0 || images.length > 0) && !disabled && !loading);
</script>

<!-- Hidden file input -->
<input
	bind:this={fileInputRef}
	type="file"
	accept="image/*"
	multiple
	class="hidden"
	onchange={handleFileChange}
/>

<div class="w-full max-w-3xl mx-auto px-4">
	<div class="rounded-3xl border bg-muted/30 shadow-sm overflow-hidden">
		<!-- Image previews -->
		{#if images.length > 0}
			<div class="flex gap-2 px-4 pt-3 flex-wrap">
				{#each images as image (image.id)}
					<div class="relative group">
						<img
							src={image.preview}
							alt="Upload preview"
							class="h-16 w-16 rounded-lg object-cover border"
						/>
						<button
							type="button"
							class="absolute -top-1.5 -right-1.5 size-5 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
							onclick={() => removeImage(image.id)}
						>
							<X class="size-3" />
						</button>
					</div>
				{/each}
			</div>
		{/if}

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
			<div class="flex items-center gap-1">
				<!-- Image upload button -->
				<Tooltip.Root>
					<Tooltip.Trigger>
						{#snippet child({ props })}
							<Button
								{...props}
								variant="ghost"
								size="icon"
								class="size-10 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted"
								onclick={handleImageSelect}
								{disabled}
							>
								<ImagePlus class="size-5" />
							</Button>
						{/snippet}
					</Tooltip.Trigger>
					<Tooltip.Portal>
						<Tooltip.Content>Add image</Tooltip.Content>
					</Tooltip.Portal>
				</Tooltip.Root>

				<!-- Thinking toggle button -->
				<Tooltip.Root>
					<Tooltip.Trigger>
						{#snippet child({ props })}
							<Button
								{...props}
								variant="ghost"
								size="icon"
								class="size-10 rounded-xl transition-colors {thinkingEnabled
									? 'bg-primary/10 text-primary hover:bg-primary/20'
									: 'text-muted-foreground hover:text-foreground hover:bg-muted'}"
								onclick={toggleThinking}
							>
								<Brain class="size-5" />
							</Button>
						{/snippet}
					</Tooltip.Trigger>
					<Tooltip.Portal>
						<Tooltip.Content>
							{thinkingEnabled ? 'Thinking mode ON' : 'Enable thinking mode'}
						</Tooltip.Content>
					</Tooltip.Portal>
				</Tooltip.Root>

				<!-- Tools dropdown -->
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Button
								{...props}
								variant="ghost"
								class="h-10 px-3 rounded-xl transition-colors {activeToolsCount > 0
									? 'bg-primary/10 text-primary hover:bg-primary/20'
									: 'text-muted-foreground hover:text-foreground hover:bg-muted'}"
							>
								<Wrench class="size-5" />
								{#if activeToolsCount > 0}
									<Badge variant="secondary" class="ml-1.5 h-5 px-1.5 text-[10px]">
										{activeToolsCount}
									</Badge>
								{/if}
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="start" class="w-[200px]">
						<DropdownMenu.Label class="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
							Tools
						</DropdownMenu.Label>
						<DropdownMenu.Item
							class="flex cursor-pointer items-center justify-between gap-2"
							onclick={toggleWebSearch}
						>
							<div class="flex items-center gap-2">
								<Globe class="size-4" />
								<span>Web Search</span>
							</div>
							{#if webSearchEnabled}
								<Check class="size-4 text-primary" />
							{/if}
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
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
