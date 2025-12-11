<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Bot } from 'lucide-svelte';

	let { data, selected } = $props<{
		data: { label: string; type: string; config: Record<string, unknown> };
		selected?: boolean;
	}>();

	let model = $derived((data.config?.model as string) || 'gemini-2.0-flash');
</script>

<div
	class="min-w-[180px] rounded-lg border-2 bg-white shadow-sm transition-all {selected
		? 'border-purple-500 shadow-md'
		: 'border-purple-300'}"
>
	<!-- Input handle -->
	<Handle type="target" position={Position.Left} class="!bg-purple-500 !size-3" />

	<!-- Header -->
	<div class="flex items-center gap-2 border-b border-purple-100 px-3 py-2">
		<div class="flex size-7 items-center justify-center rounded bg-purple-100">
			<Bot class="size-4 text-purple-600" />
		</div>
		<span class="font-medium text-purple-700">{data.label || 'LLM'}</span>
	</div>

	<!-- Body -->
	<div class="px-3 py-2">
		<div class="text-xs text-muted-foreground">Model</div>
		<div class="text-sm font-medium truncate">{model}</div>
	</div>

	<!-- Output handle -->
	<Handle type="source" position={Position.Right} class="!bg-purple-500 !size-3" />
</div>
