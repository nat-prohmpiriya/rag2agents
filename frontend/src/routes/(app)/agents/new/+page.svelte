<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { ArrowLeft, Bot, Save, Loader2 } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Label } from '$lib/components/ui/label';
	import { Switch } from '$lib/components/ui/switch';
	import * as Card from '$lib/components/ui/card';
	import * as Select from '$lib/components/ui/select';
	import { Slider } from '$lib/components/ui/slider';
	import { agentsApi, chatApi, documentsApi, projectsApi } from '$lib/api';
	import type { AgentCreate, ModelInfo, Document, Project } from '$lib/api';
	import KnowledgeBaseSelector from '$lib/components/agents/KnowledgeBaseSelector.svelte';
	import ToolSelector from '$lib/components/agents/ToolSelector.svelte';

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
	let selectedTools = $state<string[]>(['rag_search']);

	// Data
	let models = $state<ModelInfo[]>([]);
	let documents = $state<Document[]>([]);
	let projects = $state<Project[]>([]);

	// UI state
	let saving = $state(false);
	let error = $state<string | null>(null);
	let loadingData = $state(true);

	// Validation
	let isValid = $derived(
		name.trim().length > 0 &&
		name.trim().length <= 100 &&
		slug.trim().length > 0 &&
		slug.trim().length <= 50 &&
		/^[a-z0-9-]+$/.test(slug.trim())
	);

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loadingData = true;
		try {
			const [modelsRes, docsRes, projectsRes] = await Promise.all([
				chatApi.getModels(),
				documentsApi.list(1, 100),
				projectsApi.list(1, 100)
			]);
			models = modelsRes.models;
			documents = docsRes.items;
			projects = projectsRes.items;

			// Set default model
			if (models.length > 0 && !selectedModel) {
				selectedModel = models[0].id;
			}
		} catch (e) {
			console.error('Failed to load data:', e);
			error = 'Failed to load data';
		} finally {
			loadingData = false;
		}
	}

	function generateSlug(value: string): string {
		return value
			.toLowerCase()
			.replace(/\s+/g, '-')
			.replace(/[^a-z0-9-]/g, '')
			.slice(0, 50);
	}

	function handleNameChange(e: Event) {
		const input = e.target as HTMLInputElement;
		name = input.value;
		// Auto-generate slug if empty
		if (!slug || slug === generateSlug(name.slice(0, -1))) {
			slug = generateSlug(name);
		}
	}

	async function handleSubmit() {
		if (!isValid || saving) return;

		saving = true;
		error = null;

		try {
			const data: AgentCreate = {
				name: name.trim(),
				slug: slug.trim(),
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

			await agentsApi.create(data);
			goto('/agents');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create agent';
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Create Agent | RAG Agent</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-4xl">
			<!-- Header -->
			<div class="flex items-center gap-4 mb-6">
				<Button variant="ghost" size="icon" onclick={() => goto('/agents')}>
					<ArrowLeft class="size-5" />
				</Button>
				<div class="flex items-center gap-3">
					<Bot class="size-8 text-foreground" />
					<h1 class="text-3xl font-semibold text-foreground">Create Agent</h1>
				</div>
			</div>

			{#if loadingData}
				<div class="flex items-center justify-center py-12">
					<Loader2 class="size-8 animate-spin text-muted-foreground" />
				</div>
			{:else}
				<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-6">
					<!-- Basic Info -->
					<Card.Root>
						<Card.Header>
							<Card.Title>Basic Information</Card.Title>
							<Card.Description>Set up the basic details for your agent</Card.Description>
						</Card.Header>
						<Card.Content class="space-y-4">
							<!-- Name -->
							<div class="space-y-2">
								<Label for="agent-name">Name *</Label>
								<Input
									id="agent-name"
									value={name}
									oninput={handleNameChange}
									placeholder="My Research Agent"
									maxlength={100}
									disabled={saving}
								/>
							</div>

							<!-- Slug -->
							<div class="space-y-2">
								<Label for="agent-slug">Slug *</Label>
								<Input
									id="agent-slug"
									bind:value={slug}
									placeholder="my-research-agent"
									maxlength={50}
									disabled={saving}
									class={slug.length > 0 && !/^[a-z0-9-]+$/.test(slug) ? 'border-destructive' : ''}
								/>
								<p class="text-xs text-muted-foreground">
									Lowercase letters, numbers, and hyphens only. Used in URLs.
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
									disabled={saving}
								/>
							</div>

							<!-- Icon -->
							<div class="space-y-2">
								<Label for="agent-icon">Icon</Label>
								<Input
									id="agent-icon"
									bind:value={icon}
									placeholder="robot, search, brain..."
									disabled={saving}
								/>
								<p class="text-xs text-muted-foreground">
									Icon name for display (robot, search, brain, code, chart, sparkles)
								</p>
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
									disabled={saving}
								/>
							</div>
						</Card.Content>
					</Card.Root>

					<!-- System Prompt -->
					<Card.Root>
						<Card.Header>
							<Card.Title>System Prompt</Card.Title>
							<Card.Description>Instructions that define the agent's behavior and personality</Card.Description>
						</Card.Header>
						<Card.Content>
							<Textarea
								id="agent-prompt"
								bind:value={systemPrompt}
								placeholder="You are a helpful assistant that specializes in..."
								rows={6}
								disabled={saving}
								class="font-mono text-sm"
							/>
						</Card.Content>
					</Card.Root>

					<!-- Model Settings -->
					<Card.Root>
						<Card.Header>
							<Card.Title>Model Settings</Card.Title>
							<Card.Description>Configure the AI model for this agent</Card.Description>
						</Card.Header>
						<Card.Content class="space-y-6">
							<!-- Model Select -->
							<div class="space-y-2">
								<Label>Model</Label>
								<Select.Root type="single" bind:value={selectedModel}>
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
								<p class="text-xs text-muted-foreground">
									Lower values make output more focused and deterministic. Higher values make it more creative.
								</p>
							</div>
						</Card.Content>
					</Card.Root>

					<!-- Knowledge Base -->
					<Card.Root>
						<Card.Header>
							<Card.Title>Knowledge Base</Card.Title>
							<Card.Description>Select documents or projects for the agent to use as context</Card.Description>
						</Card.Header>
						<Card.Content>
							<KnowledgeBaseSelector
								{projects}
								{documents}
								bind:selectedProjectId
								bind:selectedDocumentIds
								disabled={saving}
							/>
						</Card.Content>
					</Card.Root>

					<!-- Tools -->
					<Card.Root>
						<Card.Header>
							<Card.Title>Tools</Card.Title>
							<Card.Description>Select the capabilities available to this agent</Card.Description>
						</Card.Header>
						<Card.Content>
							<ToolSelector
								bind:selectedTools
								disabled={saving}
							/>
						</Card.Content>
					</Card.Root>

					<!-- Error -->
					{#if error}
						<div class="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
							<p class="text-destructive">{error}</p>
						</div>
					{/if}

					<!-- Submit -->
					<div class="flex items-center justify-end gap-3">
						<Button type="button" variant="outline" onclick={() => goto('/agents')} disabled={saving}>
							Cancel
						</Button>
						<Button type="submit" disabled={!isValid || saving}>
							{#if saving}
								<Loader2 class="mr-2 size-4 animate-spin" />
								Creating...
							{:else}
								<Save class="mr-2 size-4" />
								Create Agent
							{/if}
						</Button>
					</div>
				</form>
			{/if}
		</div>
	</div>
</div>
