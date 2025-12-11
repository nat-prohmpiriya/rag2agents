<script lang="ts">
	import { Play, Square, Bot, Search, GitBranch, Globe, Code } from 'lucide-svelte';

	interface NodeTypeInfo {
		type: string;
		label: string;
		icon: typeof Play;
		color: string;
		description: string;
	}

	const nodeTypes: NodeTypeInfo[] = [
		{
			type: 'start',
			label: 'Start',
			icon: Play,
			color: 'green',
			description: 'Workflow entry point'
		},
		{
			type: 'end',
			label: 'End',
			icon: Square,
			color: 'red',
			description: 'Workflow exit point'
		},
		{
			type: 'llm',
			label: 'LLM',
			icon: Bot,
			color: 'purple',
			description: 'Generate text with AI'
		},
		{
			type: 'rag',
			label: 'RAG Search',
			icon: Search,
			color: 'blue',
			description: 'Search documents'
		},
		{
			type: 'agent',
			label: 'Agent',
			icon: Bot,
			color: 'orange',
			description: 'Use an AI agent'
		},
		{
			type: 'condition',
			label: 'Condition',
			icon: GitBranch,
			color: 'yellow',
			description: 'Branch logic'
		},
		{
			type: 'http',
			label: 'HTTP',
			icon: Globe,
			color: 'cyan',
			description: 'Call external API'
		}
	];

	function getColorClasses(color: string) {
		const colors: Record<string, { bg: string; border: string; text: string; iconBg: string }> = {
			green: {
				bg: 'bg-green-50',
				border: 'border-green-200 hover:border-green-400',
				text: 'text-green-700',
				iconBg: 'bg-green-100'
			},
			red: {
				bg: 'bg-red-50',
				border: 'border-red-200 hover:border-red-400',
				text: 'text-red-700',
				iconBg: 'bg-red-100'
			},
			purple: {
				bg: 'bg-purple-50',
				border: 'border-purple-200 hover:border-purple-400',
				text: 'text-purple-700',
				iconBg: 'bg-purple-100'
			},
			blue: {
				bg: 'bg-blue-50',
				border: 'border-blue-200 hover:border-blue-400',
				text: 'text-blue-700',
				iconBg: 'bg-blue-100'
			},
			orange: {
				bg: 'bg-orange-50',
				border: 'border-orange-200 hover:border-orange-400',
				text: 'text-orange-700',
				iconBg: 'bg-orange-100'
			},
			yellow: {
				bg: 'bg-yellow-50',
				border: 'border-yellow-200 hover:border-yellow-400',
				text: 'text-yellow-700',
				iconBg: 'bg-yellow-100'
			},
			cyan: {
				bg: 'bg-cyan-50',
				border: 'border-cyan-200 hover:border-cyan-400',
				text: 'text-cyan-700',
				iconBg: 'bg-cyan-100'
			}
		};
		return colors[color] || colors.purple;
	}

	function onDragStart(event: DragEvent, nodeType: string) {
		if (!event.dataTransfer) return;
		event.dataTransfer.setData('application/reactflow', nodeType);
		event.dataTransfer.effectAllowed = 'move';
	}
</script>

<div class="flex h-full w-64 flex-col border-r border-border bg-muted/30">
	<div class="border-b border-border p-4">
		<h2 class="font-semibold text-foreground">Nodes</h2>
		<p class="text-xs text-muted-foreground">Drag to canvas</p>
	</div>

	<div class="flex-1 overflow-auto p-3">
		<div class="space-y-2">
			{#each nodeTypes as node}
				{@const colors = getColorClasses(node.color)}
				<button
					class="w-full cursor-grab rounded-lg border p-3 text-left transition-all active:cursor-grabbing {colors.border} {colors.bg}"
					draggable="true"
					ondragstart={(e) => onDragStart(e, node.type)}
				>
					<div class="flex items-center gap-2">
						<div class="flex size-8 items-center justify-center rounded {colors.iconBg}">
							<node.icon class="size-4 {colors.text}" />
						</div>
						<div>
							<div class="font-medium {colors.text}">{node.label}</div>
							<div class="text-xs text-muted-foreground">{node.description}</div>
						</div>
					</div>
				</button>
			{/each}
		</div>
	</div>
</div>
