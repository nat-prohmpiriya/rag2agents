<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { GitBranch } from 'lucide-svelte';

	let { data, selected } = $props<{
		data: { label: string; type: string; config: Record<string, unknown> };
		selected?: boolean;
	}>();

	let variable = $derived((data.config?.variable as string) || '');
	let operator = $derived((data.config?.operator as string) || 'equals');
</script>

<div
	class="min-w-[180px] rounded-lg border-2 bg-white shadow-sm transition-all {selected
		? 'border-yellow-500 shadow-md'
		: 'border-yellow-300'}"
>
	<!-- Input handle -->
	<Handle type="target" position={Position.Left} class="!bg-yellow-500 !size-3" />

	<!-- Header -->
	<div class="flex items-center gap-2 border-b border-yellow-100 px-3 py-2">
		<div class="flex size-7 items-center justify-center rounded bg-yellow-100">
			<GitBranch class="size-4 text-yellow-600" />
		</div>
		<span class="font-medium text-yellow-700">{data.label || 'Condition'}</span>
	</div>

	<!-- Body -->
	<div class="px-3 py-2">
		<div class="text-xs text-muted-foreground">
			{variable || 'Configure condition'}
		</div>
		<div class="text-sm font-medium">{operator}</div>
	</div>

	<!-- Output handles -->
	<Handle
		type="source"
		position={Position.Right}
		id="true"
		class="!bg-green-500 !size-3"
		style="top: 35%"
	/>
	<Handle
		type="source"
		position={Position.Right}
		id="false"
		class="!bg-red-500 !size-3"
		style="top: 65%"
	/>

	<!-- Labels for outputs -->
	<div class="absolute right-[-35px] top-[30%] text-xs text-green-600">true</div>
	<div class="absolute right-[-35px] top-[60%] text-xs text-red-600">false</div>
</div>
