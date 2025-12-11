<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { ArrowLeft, Bot, Save, Loader2, Trash2, MessageSquare } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Label } from '$lib/components/ui/label';
	import { Switch } from '$lib/components/ui/switch';
	import * as Card from '$lib/components/ui/card';
	import * as Select from '$lib/components/ui/select';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import * as Tabs from '$lib/components/ui/tabs';
	import { Slider } from '$lib/components/ui/slider';
	import { agentsApi, chatApi, documentsApi, projectsApi } from '$lib/api';
	import type { AgentDetail, AgentUpdate, ModelInfo, Document, Project } from '$lib/api';
	import KnowledgeBaseSelector from '$lib/components/agents/KnowledgeBaseSelector.svelte';
	import ToolSelector from '$lib/components/agents/ToolSelector.svelte';

	// Get agent slug from URL
	let agentSlug = $derived($page.params.slug);

	// Agent data
	let agent = $state<AgentDetail | null>(null);

	// Form state
	let name = $state('');
	let slug = $state('');
	let description = $state('');
	let systemPrompt = $state('');
	let icon = $state('');
	let isActive = $state(true);
	let selectedModel = $state<string>('');
	let temperature = $state([0.7]);
	let selectedProjectId = $state<string | null>(null);
	let selectedDocumentIds = $state<string[]>([]);
	let selectedTools = $state<string[]>([]);

	// Data
	let models = $state<ModelInfo[]>([]);
	let documents = $state<Document[]>([]);
	let projects = $state<Project[]>([]);

	// UI state
	let saving = $state(false);
	let deleting = $state(false);
	let error = $state<string | null>(null);
	let loadingData = $state(true);
	let deleteDialogOpen = $state(false);
	let activeTab = $state('settings');

	// Validation
	let isValid = $derived(
		name.trim().length > 0 &&
		name.trim().length <= 100 &&
		slug.trim().length > 0 &&
		slug.trim().length <= 50 &&
		/^[a-z0-9-]+$/.test(slug.trim())
	);

	// Check if agent is editable (user agent, not system)
	let isEditable = $derived(agent?.source === 'user');

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		if (!agentSlug) {
			error = 'Agent slug is required';
			return;
		}

		loadingData = true;
		error = null;
		try {
			const [agentRes, modelsRes, docsRes, projectsRes] = await Promise.all([
				agentsApi.get(agentSlug),
				chatApi.getModels(),
				documentsApi.list(1, 100),
				projectsApi.list(1, 100)
			]);

			agent = agentRes;
			models = modelsRes.models;
			documents = docsRes.items;
			projects = projectsRes.items;

			// Populate form from agent data
			name = agent.name;
			slug = agent.slug;
			description = agent.description || '';
			systemPrompt = agent.system_prompt || '';
			icon = agent.icon || '';
			isActive = agent.is_active;
			selectedTools = agent.tools || [];
			selectedProjectId = agent.project_id || null;
			selectedDocumentIds = agent.document_ids || [];

			// Extract config
			const config = agent.config as Record<string, unknown> | undefined;
			if (config) {
				selectedModel = (config.model as string) || models[0]?.id || '';
				temperature = [typeof config.temperature === 'number' ? config.temperature : 0.7];
			} else {
				selectedModel = models[0]?.id || '';
				temperature = [0.7];
			}
		} catch (e) {
			console.error('Failed to load agent:', e);
			error = e instanceof Error ? e.message : 'Failed to load agent';
		} finally {
			loadingData = false;
		}
	}

	async function handleSubmit() {
		if (!isValid || saving || !isEditable) return;

		saving = true;
		error = null;

		try {
			const data: AgentUpdate = {
				name: name.trim(),
				description: description.trim() || undefined,
				system_prompt: systemPrompt.trim() || undefined,
				icon: icon.trim() || undefined,
				is_active: isActive,
				tools: selectedTools,
				project_id: selectedProjectId || undefined,
				document_ids: selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
				config: {
					model: selectedModel,
					temperature: temperature[0]
				}
			};

			if (!agent?.id) {
				throw new Error('Cannot update system agent');
			}
			await agentsApi.update(agent.id, data);
			goto('/agents');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to update agent';
		} finally {
			saving = false;
		}
	}

	async function handleDelete() {
		if (!agent?.id || deleting) return;

		deleting = true;
		try {
			await agentsApi.delete(agent.id);
			goto('/agents');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete agent';
		} finally {
			deleting = false;
			deleteDialogOpen = false;
		}
	}

	function handleChatWithAgent() {
		goto(`/chat?agent=${agent?.slug}`);
	}
</script>

<svelte:head>
	<title>{agent?.name || 'Agent'} | RAG Agent</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-4xl">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center gap-4">
					<Button variant="ghost" size="icon" onclick={() => goto('/agents')}>
						<ArrowLeft class="size-5" />
					</Button>
					<div class="flex items-center gap-3">
						<Bot class="size-8 text-foreground" />
						<div>
							<h1 class="text-3xl font-semibold text-foreground">
								{agent?.name || 'Loading...'}
							</h1>
							{#if agent?.source === 'system'}
								<span class="text-sm text-muted-foreground">System Agent (Read-only)</span>
							{/if}
						</div>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<Button variant="outline" onclick={handleChatWithAgent} disabled={!agent}>
						<MessageSquare class="mr-2 size-4" />
						Chat
					</Button>
					{#if isEditable}
						<Button
							variant="destructive"
							size="icon"
							onclick={() => deleteDialogOpen = true}
						>
							<Trash2 class="size-4" />
						</Button>
					{/if}
				</div>
			</div>

			{#if loadingData}
				<div class="flex items-center justify-center py-12">
					<Loader2 class="size-8 animate-spin text-muted-foreground" />
				</div>
			{:else if error && !agent}
				<div class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center">
					<p class="text-destructive">{error}</p>
					<Button variant="outline" class="mt-4" onclick={() => goto('/agents')}>
						Back to Agents
					</Button>
				</div>
			{:else if agent}
				<Tabs.Root bind:value={activeTab}>
					<Tabs.List class="mb-6">
						<Tabs.Trigger value="settings">Settings</Tabs.Trigger>
						<Tabs.Trigger value="knowledge">Knowledge Base</Tabs.Trigger>
						<Tabs.Trigger value="tools">Tools</Tabs.Trigger>
					</Tabs.List>

					<!-- Settings Tab -->
					<Tabs.Content value="settings">
						<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-6">
							<!-- Basic Info -->
							<Card.Root>
								<Card.Header>
									<Card.Title>Basic Information</Card.Title>
								</Card.Header>
								<Card.Content class="space-y-4">
									<!-- Name -->
									<div class="space-y-2">
										<Label for="agent-name">Name *</Label>
										<Input
											id="agent-name"
											bind:value={name}
											placeholder="My Research Agent"
											maxlength={100}
											disabled={saving || !isEditable}
										/>
									</div>

									<!-- Slug -->
									<div class="space-y-2">
										<Label for="agent-slug">Slug</Label>
										<Input
											id="agent-slug"
											value={slug}
											disabled
											class="bg-muted"
										/>
										<p class="text-xs text-muted-foreground">
											Slug cannot be changed after creation
										</p>
									</div>

									<!-- Description -->
									<div class="space-y-2">
										<Label for="agent-description">Description</Label>
										<Textarea
											id="agent-description"
											bind:value={description}
											placeholder="What this agent does..."
											rows={2}
											disabled={saving || !isEditable}
										/>
									</div>

									<!-- Icon -->
									<div class="space-y-2">
										<Label for="agent-icon">Icon</Label>
										<Input
											id="agent-icon"
											bind:value={icon}
											placeholder="robot, search, brain..."
											disabled={saving || !isEditable}
										/>
									</div>

									<!-- Active -->
									<div class="flex items-center justify-between">
										<div>
											<Label for="agent-active">Active</Label>
											<p class="text-xs text-muted-foreground">Enable or disable this agent</p>
										</div>
										<Switch
											id="agent-active"
											checked={isActive}
											onCheckedChange={(checked) => isActive = checked}
											disabled={saving || !isEditable}
										/>
									</div>
								</Card.Content>
							</Card.Root>

							<!-- System Prompt -->
							<Card.Root>
								<Card.Header>
									<Card.Title>System Prompt</Card.Title>
									<Card.Description>Instructions that define the agent's behavior</Card.Description>
								</Card.Header>
								<Card.Content>
									<Textarea
										id="agent-prompt"
										bind:value={systemPrompt}
										placeholder="You are a helpful assistant that specializes in..."
										rows={6}
										disabled={saving || !isEditable}
										class="font-mono text-sm"
									/>
								</Card.Content>
							</Card.Root>

							<!-- Model Settings -->
							<Card.Root>
								<Card.Header>
									<Card.Title>Model Settings</Card.Title>
								</Card.Header>
								<Card.Content class="space-y-6">
									<!-- Model Select -->
									<div class="space-y-2">
										<Label>Model</Label>
										<Select.Root type="single" bind:value={selectedModel} disabled={!isEditable}>
											<Select.Trigger class="w-full">
												{#if selectedModel}
													{models.find(m => m.id === selectedModel)?.name || selectedModel}
												{:else}
													Select a model
												{/if}
											</Select.Trigger>
											<Select.Content>
												{#each models as model}
													<Select.Item value={model.id}>
														<div class="flex flex-col">
															<span>{model.name}</span>
															<span class="text-xs text-muted-foreground">{model.provider}</span>
														</div>
													</Select.Item>
												{/each}
											</Select.Content>
										</Select.Root>
									</div>

									<!-- Temperature -->
									<div class="space-y-4">
										<div class="flex items-center justify-between">
											<Label>Temperature</Label>
											<span class="text-sm text-muted-foreground">{temperature[0].toFixed(2)}</span>
										</div>
										<Slider
											type="multiple"
											bind:value={temperature}
											min={0}
											max={2}
											step={0.1}
											class="cursor-pointer"
										/>
									</div>
								</Card.Content>
							</Card.Root>

							<!-- Error -->
							{#if error}
								<div class="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
									<p class="text-destructive">{error}</p>
								</div>
							{/if}

							<!-- Submit -->
							{#if isEditable}
								<div class="flex items-center justify-end gap-3">
									<Button type="button" variant="outline" onclick={() => goto('/agents')} disabled={saving}>
										Cancel
									</Button>
									<Button type="submit" disabled={!isValid || saving}>
										{#if saving}
											<Loader2 class="mr-2 size-4 animate-spin" />
											Saving...
										{:else}
											<Save class="mr-2 size-4" />
											Save Changes
										{/if}
									</Button>
								</div>
							{/if}
						</form>
					</Tabs.Content>

					<!-- Knowledge Base Tab -->
					<Tabs.Content value="knowledge">
						<Card.Root>
							<Card.Header>
								<Card.Title>Knowledge Base</Card.Title>
								<Card.Description>
									Select documents or projects for the agent to use as context
								</Card.Description>
							</Card.Header>
							<Card.Content>
								<KnowledgeBaseSelector
									{projects}
									{documents}
									bind:selectedProjectId
									bind:selectedDocumentIds
									disabled={saving || !isEditable}
								/>
							</Card.Content>
						</Card.Root>

						{#if isEditable}
							<div class="flex items-center justify-end gap-3 mt-6">
								<Button onclick={handleSubmit} disabled={!isValid || saving}>
									{#if saving}
										<Loader2 class="mr-2 size-4 animate-spin" />
										Saving...
									{:else}
										<Save class="mr-2 size-4" />
										Save Changes
									{/if}
								</Button>
							</div>
						{/if}
					</Tabs.Content>

					<!-- Tools Tab -->
					<Tabs.Content value="tools">
						<Card.Root>
							<Card.Header>
								<Card.Title>Tools</Card.Title>
								<Card.Description>
									Select the capabilities available to this agent
								</Card.Description>
							</Card.Header>
							<Card.Content>
								<ToolSelector
									bind:selectedTools
									disabled={saving || !isEditable}
								/>
							</Card.Content>
						</Card.Root>

						{#if isEditable}
							<div class="flex items-center justify-end gap-3 mt-6">
								<Button onclick={handleSubmit} disabled={!isValid || saving}>
									{#if saving}
										<Loader2 class="mr-2 size-4 animate-spin" />
										Saving...
									{:else}
										<Save class="mr-2 size-4" />
										Save Changes
									{/if}
								</Button>
							</div>
						{/if}
					</Tabs.Content>
				</Tabs.Root>
			{/if}
		</div>
	</div>
</div>

<!-- Delete Confirmation Dialog -->
<AlertDialog.Root bind:open={deleteDialogOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete Agent</AlertDialog.Title>
			<AlertDialog.Description>
				Are you sure you want to delete "{agent?.name}"? This action cannot be undone.
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
