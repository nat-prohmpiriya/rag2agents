<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Search } from 'lucide-svelte';

	let { data, selected } = $props<{
		data: { label: string; type: string; config: Record<string, unknown> };
		selected?: boolean;
	}>();

	let topK = $derived((data.config?.top_k as number) || 5);
</script>

<div
	class="min-w-[180px] rounded-lg border-2 bg-white shadow-sm transition-all {selected
		? 'border-blue-500 shadow-md'
		: 'border-blue-300'}"
>
	<!-- Input handle -->
	<Handle type="target" position={Position.Left} class="!bg-blue-500 !size-3" />

	<!-- Header -->
	<div class="flex items-center gap-2 border-b border-blue-100 px-3 py-2">
		<div class="flex size-7 items-center justify-center rounded bg-blue-100">
			<Search class="size-4 text-blue-600" />
		</div>
		<span class="font-medium text-blue-700">{data.label || 'RAG Search'}</span>
	</div>

	<!-- Body -->
	<div class="px-3 py-2">
		<div class="text-xs text-muted-foreground">Top K Results</div>
		<div class="text-sm font-medium">{topK}</div>
	</div>

	<!-- Output handle -->
	<Handle type="source" position={Position.Right} class="!bg-blue-500 !size-3" />
</div>
