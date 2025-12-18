<script lang="ts">
	import { Sparkles, Loader2, Settings2 } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Label } from '$lib/components/ui/label';
	import * as Select from '$lib/components/ui/select';
	import type { ImageModel, ImageSize } from '$lib/api';

	let {
		prompt = $bindable(''),
		selectedModel = $bindable(''),
		selectedSize = $bindable('1024x1024'),
		models,
		sizes,
		generating,
		onGenerate
	} = $props<{
		prompt: string;
		selectedModel: string;
		selectedSize: string;
		models: ImageModel[];
		sizes: ImageSize[];
		generating: boolean;
		onGenerate: () => void;
	}>();
</script>

<div class="flex flex-col gap-4">
	<!-- Prompt Input -->
	<div class="rounded-lg border bg-card p-4">
		<Label for="prompt" class="mb-2 block text-sm font-medium">Prompt</Label>
		<Textarea
			id="prompt"
			bind:value={prompt}
			placeholder="Describe the image you want to generate..."
			class="min-h-[120px] resize-none"
			disabled={generating}
		/>

		<!-- Settings -->
		<div class="mt-4 grid grid-cols-2 gap-3">
			<!-- Model -->
			<div>
				<Label class="mb-1.5 block text-xs text-muted-foreground">Model</Label>
				<Select.Root type="single" bind:value={selectedModel}>
					<Select.Trigger class="w-full">
						{models.find((m: ImageModel) => m.id === selectedModel)?.name || 'Select model'}
					</Select.Trigger>
					<Select.Content>
						{#each models as model}
							<Select.Item value={model.id}>{model.name}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>

			<!-- Size -->
			<div>
				<Label class="mb-1.5 block text-xs text-muted-foreground">Size</Label>
				<Select.Root type="single" bind:value={selectedSize}>
					<Select.Trigger class="w-full">
						{sizes.find((s: ImageSize) => s.value === selectedSize)?.label || 'Select size'}
					</Select.Trigger>
					<Select.Content>
						{#each sizes as size}
							<Select.Item value={size.value}>{size.label}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
		</div>

		<!-- Generate Button -->
		<Button
			class="mt-4 w-full"
			size="lg"
			disabled={!prompt.trim() || generating}
			onclick={onGenerate}
		>
			{#if generating}
				<Loader2 class="mr-2 size-4 animate-spin" />
				Generating...
			{:else}
				<Sparkles class="mr-2 size-4" />
				Generate Image
			{/if}
		</Button>
	</div>

	<!-- Tips -->
	<div class="rounded-lg border bg-muted/30 p-4">
		<h3 class="mb-2 text-sm font-medium flex items-center gap-2">
			<Settings2 class="size-4" />
			Tips
		</h3>
		<ul class="space-y-1 text-xs text-muted-foreground">
			<li>Be specific and descriptive in your prompt</li>
			<li>Include style references (e.g., "oil painting", "3D render")</li>
			<li>Mention lighting, mood, and composition</li>
			<li>Use negative prompts to exclude unwanted elements</li>
		</ul>
	</div>
</div>
