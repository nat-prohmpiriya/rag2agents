<script lang="ts">
	import { X } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Textarea } from '$lib/components/ui/textarea';
	import type { WorkflowNode } from '$lib/api/workflows';

	let {
		node,
		onUpdate,
		onClose
	} = $props<{
		node: WorkflowNode | null;
		onUpdate: (nodeId: string, data: Record<string, unknown>) => void;
		onClose: () => void;
	}>();

	let config = $derived(node?.data?.config || {});

	function updateConfig(key: string, value: unknown) {
		if (!node) return;
		onUpdate(node.id, {
			...node.data,
			config: { ...config, [key]: value }
		});
	}

	function updateLabel(value: string) {
		if (!node) return;
		onUpdate(node.id, {
			...node.data,
			label: value
		});
	}

	const models = [
		{ value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
		{ value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
		{ value: 'gpt-4o', label: 'GPT-4o' },
		{ value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
		{ value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet' }
	];

	const operators = [
		{ value: 'equals', label: 'Equals' },
		{ value: 'not_equals', label: 'Not Equals' },
		{ value: 'contains', label: 'Contains' },
		{ value: 'not_contains', label: 'Not Contains' },
		{ value: 'greater_than', label: 'Greater Than' },
		{ value: 'less_than', label: 'Less Than' },
		{ value: 'is_empty', label: 'Is Empty' },
		{ value: 'is_not_empty', label: 'Is Not Empty' }
	];

	const httpMethods = [
		{ value: 'GET', label: 'GET' },
		{ value: 'POST', label: 'POST' },
		{ value: 'PUT', label: 'PUT' },
		{ value: 'DELETE', label: 'DELETE' }
	];
</script>

{#if node}
	<div class="flex h-full w-80 flex-col border-l border-border bg-white">
		<!-- Header -->
		<div class="flex items-center justify-between border-b border-border p-4">
			<h3 class="font-semibold capitalize">{node.data.type} Node</h3>
			<Button variant="ghost" size="sm" class="size-8 p-0" onclick={onClose}>
				<X class="size-4" />
			</Button>
		</div>

		<!-- Content -->
		<div class="flex-1 overflow-auto p-4">
			<div class="space-y-4">
				<!-- Label (common to all) -->
				<div class="space-y-2">
					<Label for="label">Label</Label>
					<Input
						id="label"
						value={node.data.label}
						oninput={(e) => updateLabel(e.currentTarget.value)}
					/>
				</div>

				<!-- Node-specific config -->
				{#if node.data.type === 'llm'}
					<div class="space-y-2">
						<Label for="model">Model</Label>
						<select
							id="model"
							class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
							value={config.model || 'gemini-2.0-flash'}
							onchange={(e) => updateConfig('model', e.currentTarget.value)}
						>
							{#each models as model}
								<option value={model.value}>{model.label}</option>
							{/each}
						</select>
					</div>

					<div class="space-y-2">
						<Label for="system_prompt">System Prompt</Label>
						<Textarea
							id="system_prompt"
							rows={3}
							value={(config.system_prompt as string) || ''}
							oninput={(e) => updateConfig('system_prompt', e.currentTarget.value)}
							placeholder="You are a helpful assistant..."
						/>
					</div>

					<div class="space-y-2">
						<Label for="prompt">Prompt Template</Label>
						<Textarea
							id="prompt"
							rows={4}
							value={(config.prompt as string) || ''}
							oninput={(e) => updateConfig('prompt', e.currentTarget.value)}
							placeholder="Use {{input}} for variables"
						/>
						<p class="text-xs text-muted-foreground">
							Use {"{{inputs.query}}"} or {"{{nodes.node_id}}"} for variables
						</p>
					</div>

					<div class="space-y-2">
						<Label for="temperature">Temperature: {config.temperature || 0.7}</Label>
						<input
							type="range"
							id="temperature"
							min="0"
							max="2"
							step="0.1"
							value={config.temperature || 0.7}
							oninput={(e) => updateConfig('temperature', parseFloat(e.currentTarget.value))}
							class="w-full"
						/>
					</div>

				{:else if node.data.type === 'rag'}
					<div class="space-y-2">
						<Label for="query_from">Query From</Label>
						<Input
							id="query_from"
							value={(config.query_from as string) || 'inputs.query'}
							oninput={(e) => updateConfig('query_from', e.currentTarget.value)}
							placeholder="inputs.query"
						/>
					</div>

					<div class="space-y-2">
						<Label for="top_k">Top K Results: {config.top_k || 5}</Label>
						<input
							type="range"
							id="top_k"
							min="1"
							max="20"
							step="1"
							value={config.top_k || 5}
							oninput={(e) => updateConfig('top_k', parseInt(e.currentTarget.value))}
							class="w-full"
						/>
					</div>

				{:else if node.data.type === 'agent'}
					<div class="space-y-2">
						<Label for="agent_slug">Agent Slug</Label>
						<Input
							id="agent_slug"
							value={(config.agent_slug as string) || 'general'}
							oninput={(e) => updateConfig('agent_slug', e.currentTarget.value)}
							placeholder="general"
						/>
					</div>

					<div class="space-y-2">
						<Label for="input_from">Input From</Label>
						<Input
							id="input_from"
							value={(config.input_from as string) || 'inputs.query'}
							oninput={(e) => updateConfig('input_from', e.currentTarget.value)}
							placeholder="inputs.query"
						/>
					</div>

				{:else if node.data.type === 'condition'}
					<div class="space-y-2">
						<Label for="variable">Variable</Label>
						<Input
							id="variable"
							value={(config.variable as string) || ''}
							oninput={(e) => updateConfig('variable', e.currentTarget.value)}
							placeholder="nodes.llm-1.output"
						/>
					</div>

					<div class="space-y-2">
						<Label for="operator">Operator</Label>
						<select
							id="operator"
							class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
							value={config.operator || 'equals'}
							onchange={(e) => updateConfig('operator', e.currentTarget.value)}
						>
							{#each operators as op}
								<option value={op.value}>{op.label}</option>
							{/each}
						</select>
					</div>

					<div class="space-y-2">
						<Label for="value">Compare Value</Label>
						<Input
							id="value"
							value={(config.value as string) || ''}
							oninput={(e) => updateConfig('value', e.currentTarget.value)}
						/>
					</div>

				{:else if node.data.type === 'http'}
					<div class="space-y-2">
						<Label for="method">Method</Label>
						<select
							id="method"
							class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
							value={config.method || 'GET'}
							onchange={(e) => updateConfig('method', e.currentTarget.value)}
						>
							{#each httpMethods as method}
								<option value={method.value}>{method.label}</option>
							{/each}
						</select>
					</div>

					<div class="space-y-2">
						<Label for="url">URL</Label>
						<Input
							id="url"
							value={(config.url as string) || ''}
							oninput={(e) => updateConfig('url', e.currentTarget.value)}
							placeholder="https://api.example.com/data"
						/>
					</div>

					<div class="space-y-2">
						<Label for="body">Body (JSON)</Label>
						<Textarea
							id="body"
							rows={4}
							value={(config.body as string) || ''}
							oninput={(e) => updateConfig('body', e.currentTarget.value)}
							placeholder={`{"key": "value"}`}
						/>
					</div>

				{:else if node.data.type === 'start'}
					<p class="text-sm text-muted-foreground">
						Start node is the entry point of your workflow. It receives the initial inputs.
					</p>

				{:else if node.data.type === 'end'}
					<div class="space-y-2">
						<Label for="output_from">Output From</Label>
						<Input
							id="output_from"
							value={(config.output_from as string) || ''}
							oninput={(e) => updateConfig('output_from', e.currentTarget.value)}
							placeholder="Leave empty for last node output"
						/>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
