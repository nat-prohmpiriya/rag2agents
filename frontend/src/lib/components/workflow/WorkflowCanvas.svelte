<script lang="ts">
	import { SvelteFlow, Background, Controls, MiniMap, type OnConnect, type OnNodesChange, type OnEdgesChange } from '@xyflow/svelte';
	import type { Node, Edge, NodeTypes, Connection } from '@xyflow/svelte';
	import '@xyflow/svelte/dist/style.css';

	import {
		StartNode,
		EndNode,
		LLMNode,
		RAGNode,
		AgentNode,
		ConditionNode,
		HTTPNode
	} from './nodes';

	let {
		nodes = $bindable([]),
		edges = $bindable([]),
		onNodeClick
	} = $props<{
		nodes: Node[];
		edges: Edge[];
		onNodeClick?: (node: Node) => void;
	}>();

	// Custom node types
	const nodeTypes: NodeTypes = {
		startNode: StartNode,
		endNode: EndNode,
		llmNode: LLMNode,
		ragNode: RAGNode,
		agentNode: AgentNode,
		conditionNode: ConditionNode,
		httpNode: HTTPNode
	};

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

	// Handle drag over
	function onDragOver(event: DragEvent) {
		event.preventDefault();
		if (event.dataTransfer) {
			event.dataTransfer.dropEffect = 'move';
		}
	}

	// Handle drop - add new node
	function onDrop(event: DragEvent) {
		event.preventDefault();

		if (!event.dataTransfer) return;

		const type = event.dataTransfer.getData('application/reactflow');
		if (!type) return;

		// Get drop position relative to the canvas
		const target = event.currentTarget as HTMLElement;
		const bounds = target.getBoundingClientRect();
		const position = {
			x: event.clientX - bounds.left - 75,
			y: event.clientY - bounds.top - 25
		};

		const nodeTypeName = nodeTypeMap[type] || 'llmNode';
		const newNode: Node = {
			id: `${type}-${Date.now()}`,
			type: nodeTypeName,
			position,
			data: {
				label: type.charAt(0).toUpperCase() + type.slice(1),
				type,
				config: {}
			}
		};

		nodes = [...nodes, newNode];
	}

	// Handle node click
	function handleNodeClick(event: MouseEvent | TouchEvent, node: Node) {
		onNodeClick?.(node);
	}

	// Handle connection
	const handleConnect: OnConnect = (connection: Connection) => {
		const newEdge: Edge = {
			id: `e-${connection.source}-${connection.target}-${Date.now()}`,
			source: connection.source,
			target: connection.target,
			sourceHandle: connection.sourceHandle ?? undefined,
			targetHandle: connection.targetHandle ?? undefined
		};
		edges = [...edges, newEdge];
	};

	// Handle nodes change
	const handleNodesChange: OnNodesChange = (changes) => {
		for (const change of changes) {
			if (change.type === 'position' && change.position) {
				nodes = nodes.map((n) =>
					n.id === change.id ? { ...n, position: change.position! } : n
				);
			} else if (change.type === 'remove') {
				nodes = nodes.filter((n) => n.id !== change.id);
				// Also remove connected edges
				edges = edges.filter((e) => e.source !== change.id && e.target !== change.id);
			}
		}
	};

	// Handle edges change
	const handleEdgesChange: OnEdgesChange = (changes) => {
		for (const change of changes) {
			if (change.type === 'remove') {
				edges = edges.filter((e) => e.id !== change.id);
			}
		}
	};
</script>

<div
	class="h-full w-full"
	role="application"
	aria-label="Workflow canvas"
	ondragover={onDragOver}
	ondrop={onDrop}
>
	<SvelteFlow
		{nodes}
		{edges}
		{nodeTypes}
		fitView
		onconnect={handleConnect}
		onnodeclick={handleNodeClick}
		onnodeschange={handleNodesChange}
		onedgeschange={handleEdgesChange}
		defaultEdgeOptions={{
			type: 'smoothstep',
			animated: true
		}}
	>
		<Background />
		<Controls />
		<MiniMap />
	</SvelteFlow>
</div>

<style>
	:global(.svelte-flow) {
		background-color: #fafafa;
	}

	:global(.svelte-flow__edge-path) {
		stroke: #94a3b8;
		stroke-width: 2;
	}

	:global(.svelte-flow__edge.selected .svelte-flow__edge-path) {
		stroke: #3b82f6;
	}

	:global(.svelte-flow__handle) {
		width: 12px;
		height: 12px;
		border: 2px solid white;
	}
</style>
