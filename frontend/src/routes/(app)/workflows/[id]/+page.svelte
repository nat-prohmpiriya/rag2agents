<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import {
		ArrowLeft,
		Save,
		Play,
		Settings,
		Loader2
	} from 'lucide-svelte';
	import type { Node, Edge } from '@xyflow/svelte';
	import { workflowsApi, type WorkflowInfo, type WorkflowNode } from '$lib/api/workflows';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import WorkflowCanvas from '$lib/components/workflow/WorkflowCanvas.svelte';
	import NodePalette from '$lib/components/workflow/NodePalette.svelte';
	import NodeConfigPanel from '$lib/components/workflow/NodeConfigPanel.svelte';
	import WorkflowAiChat from '$lib/components/workflow/WorkflowAiChat.svelte';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Textarea } from '$lib/components/ui/textarea';

	// State
	let workflow = $state<WorkflowInfo | null>(null);
	let loading = $state(true);
	let saving = $state(false);
	let executing = $state(false);
	let error = $state<string | null>(null);

	// Canvas state
	let nodes = $state<Node[]>([]);
	let edges = $state<Edge[]>([]);

	// Selected node for config
	let selectedNode = $state<Node | null>(null);

	// Execute dialog
	let executeDialogOpen = $state(false);
	let executeInput = $state('');
	let executionResult = $state<string | null>(null);

	// Get workflow ID from URL
	let workflowId = $derived($page.params.id);

	// Node type mapping
	const nodeTypeMap: Record<string, string> = {
		start: 'startNode',
		end: 'endNode',
		llm: 'llmNode',
		rag: 'ragNode',
		agent: 'agentNode',
		condition: 'conditionNode',
		http: 'httpNode'
	};

	onMount(async () => {
		await loadWorkflow();
	});

	async function loadWorkflow() {
		loading = true;
		error = null;
		try {
			workflow = await workflowsApi.get(workflowId);

			// Convert workflow nodes to Svelte Flow format
			nodes = (workflow.nodes || []).map((n: WorkflowNode) => ({
				id: n.id,
				type: nodeTypeMap[n.data.type] || n.type,
				position: n.position,
				data: n.data
			}));

			edges = (workflow.edges || []).map((e) => ({
				id: e.id,
				source: e.source,
				target: e.target,
				sourceHandle: e.sourceHandle,
				targetHandle: e.targetHandle,
				type: e.type || 'smoothstep',
				animated: e.animated ?? true,
				label: e.label
			}));
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load workflow';
		} finally {
			loading = false;
		}
	}

	async function saveWorkflow() {
		if (!workflow) return;

		saving = true;
		try {
			// Convert back to API format
			const workflowNodes = nodes.map((n) => ({
				id: n.id,
				type: n.type || 'startNode',
				position: n.position,
				data: n.data as { label: string; type: string; config: Record<string, unknown> }
			}));

			const workflowEdges = edges.map((e) => ({
				id: e.id,
				source: e.source,
				target: e.target,
				sourceHandle: e.sourceHandle,
				targetHandle: e.targetHandle,
				type: e.type,
				animated: e.animated,
				label: e.label as string | undefined
			}));

			await workflowsApi.update(workflowId, {
				name: workflow.name,
				description: workflow.description,
				nodes: workflowNodes,
				edges: workflowEdges
			});
		} catch (e) {
			console.error('Failed to save workflow:', e);
		} finally {
			saving = false;
		}
	}

	async function executeWorkflow() {
		if (!workflow) return;

		executing = true;
		executionResult = null;
		try {
			const inputs = executeInput ? JSON.parse(executeInput) : {};
			const result = await workflowsApi.execute(workflowId, inputs);

			executionResult = JSON.stringify(result.outputs, null, 2);
		} catch (e) {
			executionResult = `Error: ${e instanceof Error ? e.message : 'Execution failed'}`;
		} finally {
			executing = false;
		}
	}

	function handleNodeClick(node: Node) {
		selectedNode = node;
	}

	function handleNodeUpdate(nodeId: string, data: Record<string, unknown>) {
		nodes = nodes.map((n) => (n.id === nodeId ? { ...n, data } : n));

		// Update selected node if it's the one being updated
		if (selectedNode?.id === nodeId) {
			selectedNode = { ...selectedNode, data };
		}
	}

	function closeConfigPanel() {
		selectedNode = null;
	}
</script>

<svelte:head>
	<title>{workflow?.name || 'Workflow'} | RAG Agent</title>
</svelte:head>

<div class="flex h-screen flex-col">
	<!-- Toolbar -->
	<div class="flex items-center justify-between border-b border-border bg-white px-4 py-2">
		<div class="flex items-center gap-4">
			<Button variant="ghost" size="sm" onclick={() => goto('/workflows')}>
				<ArrowLeft class="mr-2 size-4" />
				Back
			</Button>

			{#if workflow}
				<Input
					class="w-64 font-medium"
					bind:value={workflow.name}
					placeholder="Workflow name"
				/>
			{/if}
		</div>

		<div class="flex items-center gap-2">
			<Button variant="outline" size="sm" onclick={saveWorkflow} disabled={saving}>
				{#if saving}
					<Loader2 class="mr-2 size-4 animate-spin" />
					Saving...
				{:else}
					<Save class="mr-2 size-4" />
					Save
				{/if}
			</Button>

			<Button size="sm" onclick={() => (executeDialogOpen = true)}>
				<Play class="mr-2 size-4" />
				Run
			</Button>
		</div>
	</div>

	<!-- Main content -->
	<div class="flex flex-1 overflow-hidden">
		{#if loading}
			<div class="flex flex-1 items-center justify-center">
				<Loader2 class="size-8 animate-spin text-muted-foreground" />
			</div>
		{:else if error}
			<div class="flex flex-1 items-center justify-center">
				<div class="text-center">
					<p class="text-destructive">{error}</p>
					<Button variant="outline" class="mt-4" onclick={loadWorkflow}>
						Try Again
					</Button>
				</div>
			</div>
		{:else}
			<!-- Node Palette -->
			<NodePalette />

			<!-- Canvas -->
			<div class="flex-1">
				<WorkflowCanvas
					bind:nodes
					bind:edges
					onNodeClick={handleNodeClick}
				/>
			</div>

			<!-- Config Panel -->
			{#if selectedNode}
				<NodeConfigPanel
					node={selectedNode}
					onUpdate={handleNodeUpdate}
					onClose={closeConfigPanel}
				/>
			{/if}
		{/if}
	</div>
</div>

<!-- Execute Dialog -->
<Dialog.Root bind:open={executeDialogOpen}>
	<Dialog.Content class="max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Run Workflow</Dialog.Title>
			<Dialog.Description>
				Enter input data as JSON to execute the workflow.
			</Dialog.Description>
		</Dialog.Header>

		<div class="space-y-4 py-4">
			<div class="space-y-2">
				<label for="input" class="text-sm font-medium">Input (JSON)</label>
				<Textarea
					id="input"
					rows={5}
					bind:value={executeInput}
					placeholder={`{"query": "What is RAG?"}`}
				/>
			</div>

			{#if executionResult}
				<div class="space-y-2">
					<label class="text-sm font-medium">Result</label>
					<pre
						class="max-h-64 overflow-auto rounded-lg bg-muted p-3 text-sm"
					>{executionResult}</pre>
				</div>
			{/if}
		</div>

		<Dialog.Footer>
			<Button variant="outline" onclick={() => (executeDialogOpen = false)}>
				Close
			</Button>
			<Button onclick={executeWorkflow} disabled={executing}>
				{#if executing}
					<Loader2 class="mr-2 size-4 animate-spin" />
					Running...
				{:else}
					<Play class="mr-2 size-4" />
					Execute
				{/if}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>

<!-- Floating AI Chat -->
{#if workflowId}
	<WorkflowAiChat workflowId={workflowId} workflowName={workflow?.name || 'Workflow'} />
{/if}
