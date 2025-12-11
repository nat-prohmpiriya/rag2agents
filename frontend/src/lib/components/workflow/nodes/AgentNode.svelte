<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Bot } from 'lucide-svelte';

	let { data, selected } = $props<{
		data: { label: string; type: string; config: Record<string, unknown> };
		selected?: boolean;
	}>();

	let agentSlug = $derived((data.config?.agent_slug as string) || 'general');
</script>

<div
	class="min-w-[180px] rounded-lg border-2 bg-white shadow-sm transition-all {selected
		? 'border-orange-500 shadow-md'
		: 'border-orange-300'}"
>
	<!-- Input handle -->
	<Handle type="target" position={Position.Left} class="!bg-orange-500 !size-3" />

	<!-- Header -->
	<div class="flex items-center gap-2 border-b border-orange-100 px-3 py-2">
		<div class="flex size-7 items-center justify-center rounded bg-orange-100">
			<Bot class="size-4 text-orange-600" />
		</div>
		<span class="font-medium text-orange-700">{data.label || 'Agent'}</span>
	</div>

	<!-- Body -->
	<div class="px-3 py-2">
		<div class="text-xs text-muted-foreground">Agent</div>
		<div class="text-sm font-medium truncate">{agentSlug}</div>
	</div>

	<!-- Output handle -->
	<Handle type="source" position={Position.Right} class="!bg-orange-500 !size-3" />
</div>
