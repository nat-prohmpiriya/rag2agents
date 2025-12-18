<script lang="ts">
	import { Search, Calculator, Globe, Database, Code, FileSearch } from 'lucide-svelte';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { Badge } from '$lib/components/ui/badge';

	interface Props {
		selectedTools: string[];
		disabled?: boolean;
	}

	let {
		selectedTools = $bindable([]),
		disabled = false
	}: Props = $props();

	interface ToolDefinition {
		id: string;
		name: string;
		description: string;
		icon: typeof Search;
		recommended?: boolean;
	}

	const availableTools: ToolDefinition[] = [
		{
			id: 'rag_search',
			name: 'RAG Search',
			description: 'Search and retrieve relevant information from the knowledge base',
			icon: FileSearch,
			recommended: true
		},
		{
			id: 'web_search',
			name: 'Web Search',
			description: 'Search the web for current information',
			icon: Globe
		},
		{
			id: 'calculator',
			name: 'Calculator',
			description: 'Perform mathematical calculations',
			icon: Calculator
		},
		{
			id: 'code_interpreter',
			name: 'Code Interpreter',
			description: 'Execute Python code for data analysis and computations',
			icon: Code
		},
		{
			id: 'database_query',
			name: 'Database Query',
			description: 'Query connected databases for information',
			icon: Database
		}
	];

	function toggleTool(toolId: string) {
		if (disabled) return;
		if (selectedTools.includes(toolId)) {
			selectedTools = selectedTools.filter(id => id !== toolId);
		} else {
			selectedTools = [...selectedTools, toolId];
		}
	}
</script>

<div class="space-y-2">
	{#each availableTools as tool (tool.id)}
		<button
			type="button"
			class="w-full flex items-start gap-3 p-3 rounded-lg border transition-colors text-left
				{selectedTools.includes(tool.id)
					? 'border-primary bg-primary/5'
					: 'border-border hover:border-muted-foreground/50 hover:bg-muted/50'}
				{disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}"
			onclick={() => toggleTool(tool.id)}
			{disabled}
		>
			<Checkbox
				checked={selectedTools.includes(tool.id)}
				disabled={disabled}
				class="mt-0.5"
			/>
			<div class="flex-1">
				<div class="flex items-center gap-2">
					<tool.icon class="size-4 text-muted-foreground" />
					<span class="font-medium">{tool.name}</span>
					{#if tool.recommended}
						<Badge variant="secondary" class="text-xs">Recommended</Badge>
					{/if}
				</div>
				<p class="text-xs text-muted-foreground mt-1">{tool.description}</p>
			</div>
		</button>
	{/each}

	<p class="text-xs text-muted-foreground mt-4">
		Selected tools determine what capabilities your agent can use during conversations.
	</p>
</div>
