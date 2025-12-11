<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Globe } from 'lucide-svelte';

	let { data, selected } = $props<{
		data: { label: string; type: string; config: Record<string, unknown> };
		selected?: boolean;
	}>();

	let method = $derived((data.config?.method as string) || 'GET');
	let url = $derived((data.config?.url as string) || '');
</script>

<div
	class="min-w-[180px] rounded-lg border-2 bg-white shadow-sm transition-all {selected
		? 'border-cyan-500 shadow-md'
		: 'border-cyan-300'}"
>
	<!-- Input handle -->
	<Handle type="target" position={Position.Left} class="!bg-cyan-500 !size-3" />

	<!-- Header -->
	<div class="flex items-center gap-2 border-b border-cyan-100 px-3 py-2">
		<div class="flex size-7 items-center justify-center rounded bg-cyan-100">
			<Globe class="size-4 text-cyan-600" />
		</div>
		<span class="font-medium text-cyan-700">{data.label || 'HTTP Request'}</span>
	</div>

	<!-- Body -->
	<div class="px-3 py-2">
		<div class="flex items-center gap-2">
			<span
				class="rounded bg-cyan-100 px-1.5 py-0.5 text-xs font-medium text-cyan-700"
			>
				{method}
			</span>
		</div>
		<div class="mt-1 truncate text-xs text-muted-foreground">
			{url || 'Configure URL'}
		</div>
	</div>

	<!-- Output handle -->
	<Handle type="source" position={Position.Right} class="!bg-cyan-500 !size-3" />
</div>
