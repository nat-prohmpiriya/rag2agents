<script lang="ts">
	import { X, ChevronLeft, ChevronRight, Calendar, Cpu, Maximize2, Download } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import * as Dialog from '$lib/components/ui/dialog';
	import type { ImageItem } from './types';

	let {
		open = $bindable(false),
		images,
		currentIndex = $bindable(0)
	} = $props<{
		open: boolean;
		images: ImageItem[];
		currentIndex: number;
	}>();

	let currentImage = $derived(images[currentIndex] || null);

	function close() {
		open = false;
	}

	function next() {
		if (currentIndex < images.length - 1) {
			currentIndex++;
		}
	}

	function prev() {
		if (currentIndex > 0) {
			currentIndex--;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (!open) return;

		switch (e.key) {
			case 'Escape':
				close();
				break;
			case 'ArrowLeft':
				prev();
				break;
			case 'ArrowRight':
				next();
				break;
		}
	}

	function download() {
		if (!currentImage) return;

		if (currentImage.url.startsWith('data:')) {
			const link = document.createElement('a');
			link.href = currentImage.url;
			link.download = `generated-image-${currentImage.id}.png`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		} else {
			window.open(currentImage.url, '_blank');
		}
	}

	function formatDate(date: Date): string {
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<Dialog.Root bind:open>
	<Dialog.Content class="max-w-6xl border-none bg-transparent p-0 shadow-none">
		{#if currentImage}
			<div class="relative flex flex-col items-center">
				<!-- Close button -->
				<button
					type="button"
					class="absolute -top-12 right-0 rounded-full bg-black/50 p-2 text-white transition-colors hover:bg-black/70"
					onclick={close}
				>
					<X class="size-6" />
				</button>

				<!-- Navigation buttons -->
				{#if currentIndex > 0}
					<button
						type="button"
						class="absolute left-4 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-3 text-white transition-colors hover:bg-black/70"
						onclick={prev}
					>
						<ChevronLeft class="size-8" />
					</button>
				{/if}

				{#if currentIndex < images.length - 1}
					<button
						type="button"
						class="absolute right-4 top-1/2 -translate-y-1/2 rounded-full bg-black/50 p-3 text-white transition-colors hover:bg-black/70"
						onclick={next}
					>
						<ChevronRight class="size-8" />
					</button>
				{/if}

				<!-- Image -->
				<div class="max-h-[70vh] overflow-hidden rounded-lg">
					<img
						src={currentImage.url}
						alt={currentImage.prompt}
						class="max-h-[70vh] w-auto object-contain"
					/>
				</div>

				<!-- Image Info Panel -->
				<div class="mt-4 w-full max-w-2xl rounded-lg bg-card/95 p-4 backdrop-blur">
					<!-- Prompt -->
					<p class="text-sm text-foreground">"{currentImage.prompt}"</p>

					<!-- Meta info -->
					<div class="mt-3 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
						<div class="flex items-center gap-1.5">
							<Cpu class="size-3.5" />
							<span>{currentImage.model}</span>
						</div>
						<div class="flex items-center gap-1.5">
							<Maximize2 class="size-3.5" />
							<span>{currentImage.size}</span>
						</div>
						<div class="flex items-center gap-1.5">
							<Calendar class="size-3.5" />
							<span>{formatDate(currentImage.createdAt)}</span>
						</div>
					</div>

					<!-- Actions -->
					<div class="mt-4 flex gap-2">
						<Button variant="outline" size="sm" onclick={download}>
							<Download class="mr-2 size-4" />
							Download
						</Button>
						<span class="ml-auto text-xs text-muted-foreground">
							{currentIndex + 1} / {images.length}
						</span>
					</div>
				</div>

				<!-- Keyboard hints -->
				<div class="mt-3 flex items-center gap-4 text-xs text-muted-foreground/70">
					<span><kbd class="rounded bg-muted px-1.5 py-0.5">←</kbd> Previous</span>
					<span><kbd class="rounded bg-muted px-1.5 py-0.5">→</kbd> Next</span>
					<span><kbd class="rounded bg-muted px-1.5 py-0.5">ESC</kbd> Close</span>
				</div>
			</div>
		{/if}
	</Dialog.Content>
</Dialog.Root>
