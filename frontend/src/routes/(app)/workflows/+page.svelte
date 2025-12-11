<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { Workflow, Plus, Search, MoreVertical, Copy, Trash2, Play } from 'lucide-svelte';
	import { workflowsApi, type WorkflowInfo } from '$lib/api/workflows';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import WorkflowAiChat from '$lib/components/workflow/WorkflowAiChat.svelte';

	// State
	let workflows = $state<WorkflowInfo[]>([]);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let searchQuery = $state('');
	let initialized = $state(false);

	// Delete confirmation
	let deleteDialogOpen = $state(false);
	let workflowToDelete = $state<WorkflowInfo | null>(null);
	let deleting = $state(false);

	// Filtered workflows
	let filteredWorkflows = $derived.by(() => {
		if (!searchQuery.trim()) return workflows;
		const query = searchQuery.toLowerCase();
		return workflows.filter(
			(w) =>
				w.name.toLowerCase().includes(query) ||
				(w.description?.toLowerCase().includes(query) ?? false)
		);
	});

	// Use $effect to load data when component mounts in browser
	$effect(() => {
		if (browser && !initialized) {
			initialized = true;
			fetchWorkflows();
		}
	});

	async function fetchWorkflows() {
		loading = true;
		error = null;
		try {
			const response = await workflowsApi.list();
			workflows = response.workflows;
		} catch (e) {
			console.error('[Workflows] Error:', e);
			error = e instanceof Error ? e.message : 'Failed to load workflows';
		} finally {
			loading = false;
		}
	}

	async function createWorkflow() {
		try {
			const workflow = await workflowsApi.create({
				name: 'Untitled Workflow',
				description: '',
				nodes: [
					{
						id: 'start-1',
						type: 'startNode',
						position: { x: 100, y: 200 },
						data: { label: 'Start', type: 'start', config: {} }
					},
					{
						id: 'end-1',
						type: 'endNode',
						position: { x: 500, y: 200 },
						data: { label: 'End', type: 'end', config: {} }
					}
				],
				edges: [{ id: 'e-start-end', source: 'start-1', target: 'end-1' }]
			});
			goto(`/workflows/${workflow.id}`);
		} catch (e) {
			console.error('Failed to create workflow:', e);
		}
	}

	async function duplicateWorkflow(workflow: WorkflowInfo) {
		try {
			const duplicated = await workflowsApi.duplicate(workflow.id);
			workflows = [duplicated, ...workflows];
		} catch (e) {
			console.error('Failed to duplicate workflow:', e);
		}
	}

	function openDeleteDialog(workflow: WorkflowInfo) {
		workflowToDelete = workflow;
		deleteDialogOpen = true;
	}

	async function handleDelete() {
		if (!workflowToDelete) return;

		deleting = true;
		try {
			await workflowsApi.delete(workflowToDelete.id);
			workflows = workflows.filter((w) => w.id !== workflowToDelete?.id);
			deleteDialogOpen = false;
			workflowToDelete = null;
		} catch (e) {
			console.error('Failed to delete workflow:', e);
		} finally {
			deleting = false;
		}
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'active':
				return 'bg-green-100 text-green-700';
			case 'draft':
				return 'bg-yellow-100 text-yellow-700';
			case 'archived':
				return 'bg-gray-100 text-gray-700';
			default:
				return 'bg-gray-100 text-gray-700';
		}
	}
</script>

<svelte:head>
	<title>Workflows | RAG Agent</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-6xl">
			<!-- Header -->
			<div class="mb-6 flex items-center justify-between">
				<div class="flex items-center gap-3">
					<Workflow class="size-8 text-foreground" />
					<h1 class="text-3xl font-semibold text-foreground">Workflows</h1>
				</div>
				<Button onclick={createWorkflow}>
					<Plus class="mr-2 size-4" />
					New Workflow
				</Button>
			</div>

			<!-- Search -->
			<div class="relative mb-6">
				<Search
					class="absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted-foreground"
				/>
				<Input
					type="search"
					placeholder="Search workflows..."
					class="h-12 rounded-lg border-border bg-white pl-12 text-base"
					bind:value={searchQuery}
				/>
			</div>

			<!-- Content -->
			<div class="space-y-4">
				{#if loading}
					<div class="flex items-center justify-center py-12">
						<div
							class="size-8 animate-spin rounded-full border-4 border-muted border-t-primary"
						></div>
					</div>
				{:else if error}
					<div
						class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center"
					>
						<p class="text-destructive">{error}</p>
					</div>
				{:else if filteredWorkflows.length === 0}
					<div
						class="flex flex-col items-center rounded-lg border border-border bg-white p-12"
					>
						<Workflow class="size-12 text-muted-foreground/50" />
						<h3 class="mt-4 text-lg font-medium">
							{#if searchQuery}
								No workflows found
							{:else}
								No workflows yet
							{/if}
						</h3>
						<p class="mt-1 text-sm text-muted-foreground">
							{#if searchQuery}
								No workflows matching "{searchQuery}". Try a different search.
							{:else}
								Create your first workflow to get started with visual automation.
							{/if}
						</p>
						{#if !searchQuery}
							<Button class="mt-4" onclick={createWorkflow}>
								<Plus class="mr-2 size-4" />
								Create Workflow
							</Button>
						{/if}
					</div>
				{:else}
					<!-- Workflow Grid -->
					<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
						{#each filteredWorkflows as workflow (workflow.id)}
							<div
								class="group relative cursor-pointer rounded-lg border border-border bg-white p-4 transition-all hover:border-primary/50 hover:shadow-md"
								onclick={() => goto(`/workflows/${workflow.id}`)}
								onkeydown={(e) => e.key === 'Enter' && goto(`/workflows/${workflow.id}`)}
								role="button"
								tabindex="0"
							>
								<!-- Header -->
								<div class="mb-3 flex items-start justify-between">
									<div class="flex-1">
										<h3 class="font-medium text-foreground line-clamp-1">
											{workflow.name}
										</h3>
									</div>

									<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
									<div onclick={(e) => e.stopPropagation()}>
									<DropdownMenu.Root>
										<DropdownMenu.Trigger>
											{#snippet child({ props })}
												<Button
													{...props}
													variant="ghost"
													size="sm"
													class="size-8 p-0 opacity-0 group-hover:opacity-100"
												>
													<MoreVertical class="size-4" />
												</Button>
											{/snippet}
										</DropdownMenu.Trigger>
										<DropdownMenu.Content align="end">
											<DropdownMenu.Item
												onclick={() => goto(`/workflows/${workflow.id}`)}
											>
												<Play class="mr-2 size-4" />
												Open Editor
											</DropdownMenu.Item>
											<DropdownMenu.Item
												onclick={() => duplicateWorkflow(workflow)}
											>
												<Copy class="mr-2 size-4" />
												Duplicate
											</DropdownMenu.Item>
											<DropdownMenu.Separator />
											<DropdownMenu.Item
												class="text-destructive"
												onclick={() => openDeleteDialog(workflow)}
											>
												<Trash2 class="mr-2 size-4" />
												Delete
											</DropdownMenu.Item>
										</DropdownMenu.Content>
									</DropdownMenu.Root>
									</div>
								</div>

								<!-- Description -->
								<p class="mb-3 text-sm text-muted-foreground line-clamp-2">
									{workflow.description || 'No description'}
								</p>

								<!-- Footer -->
								<div
									class="flex items-center justify-between text-xs text-muted-foreground"
								>
									<span
										class={`rounded-full px-2 py-0.5 ${getStatusColor(workflow.status)}`}
									>
										{workflow.status}
									</span>
									<span>{formatDate(workflow.updated_at)}</span>
								</div>

								<!-- Node count -->
								<div
									class="mt-2 flex items-center gap-2 text-xs text-muted-foreground"
								>
									<span>{workflow.nodes?.length || 0} nodes</span>
									<span>-</span>
									<span>{workflow.edges?.length || 0} connections</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<!-- Delete Confirmation Dialog -->
<AlertDialog.Root bind:open={deleteDialogOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete Workflow</AlertDialog.Title>
			<AlertDialog.Description>
				Are you sure you want to delete "{workflowToDelete?.name}"? This action cannot be
				undone.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={deleting}>Cancel</AlertDialog.Cancel>
			<AlertDialog.Action
				class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
				disabled={deleting}
				onclick={handleDelete}
			>
				{deleting ? 'Deleting...' : 'Delete'}
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>

<!-- Floating AI Chat -->
<WorkflowAiChat workflowId="general" workflowName="Workflows" />
