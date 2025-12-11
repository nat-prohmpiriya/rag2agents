<script lang="ts">
	import { FileText, FolderOpen, Check, Search } from 'lucide-svelte';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import * as Tabs from '$lib/components/ui/tabs';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import type { Document, Project } from '$lib/api';

	interface Props {
		projects: Project[];
		documents: Document[];
		selectedProjectId: string | null;
		selectedDocumentIds: string[];
		disabled?: boolean;
	}

	let {
		projects,
		documents,
		selectedProjectId = $bindable(null),
		selectedDocumentIds = $bindable([]),
		disabled = false
	}: Props = $props();

	let searchQuery = $state('');
	let activeTab = $state('documents');

	// Filter documents based on search
	let filteredDocuments = $derived.by(() => {
		if (!searchQuery.trim()) return documents;
		const query = searchQuery.toLowerCase();
		return documents.filter(d =>
			d.filename.toLowerCase().includes(query) ||
			(d.description?.toLowerCase().includes(query) ?? false)
		);
	});

	// Filter projects based on search
	let filteredProjects = $derived.by(() => {
		if (!searchQuery.trim()) return projects;
		const query = searchQuery.toLowerCase();
		return projects.filter(p =>
			p.name.toLowerCase().includes(query) ||
			(p.description?.toLowerCase().includes(query) ?? false)
		);
	});

	// Count selected items
	let selectedCount = $derived(
		selectedProjectId ? 1 : selectedDocumentIds.length
	);

	function toggleDocument(docId: string) {
		if (disabled) return;
		// Clear project selection when selecting documents
		if (selectedProjectId) {
			selectedProjectId = null;
		}
		if (selectedDocumentIds.includes(docId)) {
			selectedDocumentIds = selectedDocumentIds.filter(id => id !== docId);
		} else {
			selectedDocumentIds = [...selectedDocumentIds, docId];
		}
	}

	function selectProject(projectId: string) {
		if (disabled) return;
		// Clear document selection when selecting a project
		selectedDocumentIds = [];
		selectedProjectId = selectedProjectId === projectId ? null : projectId;
	}

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function getStatusColor(status: string): string {
		switch (status) {
			case 'ready': return 'bg-green-500';
			case 'processing': return 'bg-yellow-500';
			case 'error': return 'bg-red-500';
			default: return 'bg-gray-500';
		}
	}
</script>

<div class="space-y-4">
	<!-- Search -->
	<div class="relative">
		<Search class="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
		<Input
			type="search"
			placeholder="Search documents or projects..."
			class="pl-10"
			bind:value={searchQuery}
			{disabled}
		/>
	</div>

	<!-- Selection summary -->
	{#if selectedCount > 0}
		<div class="flex items-center gap-2 text-sm text-muted-foreground">
			<Check class="size-4 text-green-500" />
			{#if selectedProjectId}
				<span>1 project selected</span>
			{:else}
				<span>{selectedDocumentIds.length} document{selectedDocumentIds.length !== 1 ? 's' : ''} selected</span>
			{/if}
		</div>
	{/if}

	<!-- Tabs -->
	<Tabs.Root bind:value={activeTab}>
		<Tabs.List class="grid w-full grid-cols-2">
			<Tabs.Trigger value="documents">
				<FileText class="mr-2 size-4" />
				Documents ({documents.length})
			</Tabs.Trigger>
			<Tabs.Trigger value="projects">
				<FolderOpen class="mr-2 size-4" />
				Projects ({projects.length})
			</Tabs.Trigger>
		</Tabs.List>

		<!-- Documents Tab -->
		<Tabs.Content value="documents" class="mt-4">
			{#if filteredDocuments.length === 0}
				<div class="text-center py-8 text-muted-foreground">
					{#if searchQuery}
						No documents matching "{searchQuery}"
					{:else}
						No documents available. Upload documents first.
					{/if}
				</div>
			{:else}
				<div class="space-y-2 max-h-[300px] overflow-y-auto pr-2">
					{#each filteredDocuments as doc (doc.id)}
						<button
							type="button"
							class="w-full flex items-center gap-3 p-3 rounded-lg border transition-colors text-left
								{selectedDocumentIds.includes(doc.id)
									? 'border-primary bg-primary/5'
									: 'border-border hover:border-muted-foreground/50 hover:bg-muted/50'}
								{disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}"
							onclick={() => toggleDocument(doc.id)}
							{disabled}
						>
							<Checkbox
								checked={selectedDocumentIds.includes(doc.id)}
								disabled={disabled}
							/>
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2">
									<span class="font-medium truncate">{doc.filename}</span>
									<span class="size-2 rounded-full {getStatusColor(doc.status)}"></span>
								</div>
								{#if doc.description}
									<p class="text-xs text-muted-foreground truncate">{doc.description}</p>
								{/if}
								<div class="flex items-center gap-2 mt-1">
									<Badge variant="outline" class="text-xs">
										{doc.file_type}
									</Badge>
									<span class="text-xs text-muted-foreground">
										{formatFileSize(doc.file_size)}
									</span>
									{#if doc.chunk_count > 0}
										<span class="text-xs text-muted-foreground">
											{doc.chunk_count} chunks
										</span>
									{/if}
								</div>
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</Tabs.Content>

		<!-- Projects Tab -->
		<Tabs.Content value="projects" class="mt-4">
			{#if filteredProjects.length === 0}
				<div class="text-center py-8 text-muted-foreground">
					{#if searchQuery}
						No projects matching "{searchQuery}"
					{:else}
						No projects available. Create a project first.
					{/if}
				</div>
			{:else}
				<div class="space-y-2 max-h-[300px] overflow-y-auto pr-2">
					{#each filteredProjects as project (project.id)}
						<button
							type="button"
							class="w-full flex items-center gap-3 p-3 rounded-lg border transition-colors text-left
								{selectedProjectId === project.id
									? 'border-primary bg-primary/5'
									: 'border-border hover:border-muted-foreground/50 hover:bg-muted/50'}
								{disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}"
							onclick={() => selectProject(project.id)}
							{disabled}
						>
							<div class="size-5 rounded-full border-2 flex items-center justify-center
								{selectedProjectId === project.id ? 'border-primary bg-primary' : 'border-muted-foreground/50'}">
								{#if selectedProjectId === project.id}
									<Check class="size-3 text-primary-foreground" />
								{/if}
							</div>
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2">
									<FolderOpen class="size-4 text-muted-foreground" />
									<span class="font-medium">{project.name}</span>
								</div>
								{#if project.description}
									<p class="text-xs text-muted-foreground truncate mt-1">{project.description}</p>
								{/if}
							</div>
						</button>
					{/each}
				</div>
			{/if}

			<p class="text-xs text-muted-foreground mt-4">
				Selecting a project will use all documents within that project as the knowledge base.
			</p>
		</Tabs.Content>
	</Tabs.Root>
</div>
