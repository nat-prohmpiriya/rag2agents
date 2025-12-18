<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Square } from 'lucide-svelte';

	let { data, selected } = $props<{
		data: { label: string; type: string; config: Record<string, unknown> };
		selected?: boolean;
	}>();
</script>

<div
	class="rounded-lg border-2 bg-white px-4 py-3 shadow-sm transition-all {selected
		? 'border-red-500 shadow-md'
		: 'border-red-300'}"
>
	<!-- Input handle -->
	<Handle type="target" position={Position.Left} class="!bg-red-500 !size-3" />

	<div class="flex items-center gap-2">
		<div class="flex size-8 items-center justify-center rounded-full bg-red-100">
			<Square class="size-4 text-red-600" />
		</div>
		<span class="font-medium text-red-700">{data.label || 'End'}</span>
	</div>
</div>
