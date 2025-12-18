<script lang="ts">
	import { Image, Download, Trash2, RefreshCw, Loader2, Maximize2 } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Label } from '$lib/components/ui/label';
	import type { ImageItem } from './types';

	let {
		image,
		generating,
		onOpenLightbox,
		onDownload,
		onDelete,
		onRegenerate
	} = $props<{
		image: ImageItem | null;
		generating: boolean;
		onOpenLightbox: () => void;
		onDownload: () => void;
		onDelete: () => void;
		onRegenerate: () => void;
	}>();
</script>

<div class="rounded-lg border bg-card p-4">
	<Label class="mb-3 block text-sm font-medium">Generated Image</Label>

	{#if generating}
		<!-- Loading State -->
		<div
			class="flex aspect-square items-center justify-center rounded-lg border-2 border-dashed bg-muted/30"
		>
			<div class="text-center">
				<Loader2 class="mx-auto size-12 animate-spin text-primary" />
				<p class="mt-4 text-sm text-muted-foreground">Generating your image...</p>
				<p class="mt-1 text-xs text-muted-foreground">This may take a few seconds</p>
			</div>
		</div>
	{:else if image}
		<!-- Image Display -->
		<button
			type="button"
			class="group relative w-full overflow-hidden rounded-lg border transition-all hover:ring-2 hover:ring-primary"
			onclick={onOpenLightbox}
		>
			<img
				src={image.url}
				alt={image.prompt}
				class="aspect-square w-full object-cover"
			/>
			<div class="absolute inset-0 flex items-center justify-center bg-black/0 transition-all group-hover:bg-black/20">
				<Maximize2 class="size-8 text-white opacity-0 transition-opacity group-hover:opacity-100" />
			</div>
		</button>

		<!-- Image Info -->
		<div class="mt-3 space-y-2">
			<p class="line-clamp-2 text-sm text-muted-foreground">
				"{image.prompt}"
			</p>
			<div class="flex items-center gap-2 text-xs text-muted-foreground">
				<span class="rounded bg-muted px-1.5 py-0.5">{image.model}</span>
				<span class="rounded bg-muted px-1.5 py-0.5">{image.size}</span>
			</div>
		</div>

		<!-- Action Buttons -->
		<div class="mt-4 flex gap-2">
			<Button variant="outline" size="sm" class="flex-1" onclick={onDownload}>
				<Download class="mr-2 size-4" />
				Download
			</Button>
			<Button variant="outline" size="sm" class="flex-1 text-destructive hover:text-destructive" onclick={onDelete}>
				<Trash2 class="mr-2 size-4" />
				Delete
			</Button>
			<Button variant="outline" size="sm" onclick={onRegenerate} disabled={generating}>
				<RefreshCw class="size-4" />
			</Button>
		</div>
	{:else}
		<!-- Empty State -->
		<div
			class="flex aspect-square items-center justify-center rounded-lg border-2 border-dashed bg-muted/30"
		>
			<div class="text-center">
				<Image class="mx-auto size-12 text-muted-foreground/50" />
				<p class="mt-4 text-sm text-muted-foreground">No image generated yet</p>
				<p class="mt-1 text-xs text-muted-foreground">
					Enter a prompt and click Generate
				</p>
			</div>
		</div>
	{/if}
</div>
