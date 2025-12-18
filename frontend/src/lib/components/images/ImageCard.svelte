<script lang="ts">
	import { Trash2 } from 'lucide-svelte';
	import type { ImageItem } from './types';

	let {
		image,
		onClick,
		onDelete
	} = $props<{
		image: ImageItem;
		onClick: () => void;
		onDelete: () => void;
	}>();

	function handleDeleteClick(e: MouseEvent) {
		e.stopPropagation();
		onDelete();
	}
</script>

<div class="group relative">
	<button
		type="button"
		class="aspect-square w-full overflow-hidden rounded-lg border bg-card transition-all hover:ring-2 hover:ring-primary"
		onclick={onClick}
	>
		<img src={image.url} alt={image.prompt} class="size-full object-cover" />
		<div
			class="absolute inset-0 flex items-end bg-gradient-to-t from-black/60 to-transparent opacity-0 transition-opacity group-hover:opacity-100"
		>
			<p class="line-clamp-2 p-2 text-xs text-white">{image.prompt}</p>
		</div>
	</button>
	<button
		type="button"
		class="absolute top-1 right-1 rounded-full bg-black/50 p-1 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-destructive"
		onclick={handleDeleteClick}
	>
		<Trash2 class="size-3 text-white" />
	</button>
</div>
