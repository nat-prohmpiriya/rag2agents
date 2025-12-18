<script lang="ts">
	import { Separator } from '$lib/components/ui/separator';
	import ImageCard from './ImageCard.svelte';
	import type { ImageItem } from './types';

	let {
		images,
		total,
		onImageClick,
		onImageDelete
	} = $props<{
		images: ImageItem[];
		total: number;
		onImageClick: (index: number) => void;
		onImageDelete: (image: ImageItem) => void;
	}>();
</script>

{#if images.length > 0}
	<Separator class="my-8" />

	<div>
		<div class="mb-4 flex items-center justify-between">
			<h2 class="text-lg font-medium">History</h2>
			<span class="text-sm text-muted-foreground">{total} images</span>
		</div>

		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
			{#each images as image, i (image.id)}
				<ImageCard
					{image}
					onClick={() => onImageClick(i)}
					onDelete={() => onImageDelete(image)}
				/>
			{/each}
		</div>
	</div>
{/if}
