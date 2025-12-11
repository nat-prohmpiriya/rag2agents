<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Play } from 'lucide-svelte';

	let { data, selected } = $props<{
		data: { label: string; type: string; config: Record<string, unknown> };
		selected?: boolean;
	}>();
</script>

<div
	class="rounded-lg border-2 bg-white px-4 py-3 shadow-sm transition-all {selected
		? 'border-green-500 shadow-md'
		: 'border-green-300'}"
>
	<div class="flex items-center gap-2">
		<div class="flex size-8 items-center justify-center rounded-full bg-green-100">
			<Play class="size-4 text-green-600" />
		</div>
		<span class="font-medium text-green-700">{data.label || 'Start'}</span>
	</div>

	<!-- Output handle -->
	<Handle type="source" position={Position.Right} class="!bg-green-500 !size-3" />
</div>
