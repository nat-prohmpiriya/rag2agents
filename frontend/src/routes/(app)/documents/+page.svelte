<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { FileText, Search } from 'lucide-svelte';
	import { Input } from '$lib/components/ui/input';
	import * as Select from '$lib/components/ui/select';
	import { documentsApi, type Document, type DocumentStatus } from '$lib/api/documents';
	import DocumentUpload from '$lib/components/documents/DocumentUpload.svelte';
	import DocumentCard from '$lib/components/documents/DocumentCard.svelte';
	import DocumentEditDialog from '$lib/components/documents/DocumentEditDialog.svelte';
	import * as m from '$lib/paraglide/messages';

	type StatusFilter = 'all' | DocumentStatus;

	let documents = $state<Document[]>([]);
	let loading = $state(true);
	let searchQuery = $state('');
	let statusFilter = $state<StatusFilter>('all');
	let pollInterval = $state<ReturnType<typeof setInterval> | null>(null);

	// Edit dialog state
	let editDialogOpen = $state(false);
	let editingDocument = $state<Document | null>(null);

	// Derived filter options for i18n reactivity
	let filterOptions = $derived<{ value: StatusFilter; label: string }[]>([
		{ value: 'all', label: m.common_all() },
		{ value: 'ready', label: m.documents_status_ready() },
		{ value: 'processing', label: m.documents_status_processing() },
		{ value: 'pending', label: m.documents_status_pending() },
		{ value: 'error', label: m.documents_status_error() }
	]);

	let filteredDocuments = $derived(() => {
		let result = documents;

		// Filter by search query
		if (searchQuery.trim()) {
			const query = searchQuery.toLowerCase();
			result = result.filter((doc) =>
				doc.filename.toLowerCase().includes(query)
			);
		}

		// Filter by status
		if (statusFilter !== 'all') {
			result = result.filter((doc) => doc.status === statusFilter);
		}

		return result;
	});

	let hasProcessingDocuments = $derived(
		documents.some((doc) => doc.status === 'processing' || doc.status === 'pending')
	);

	onMount(async () => {
		await loadDocuments();
	});

	onDestroy(() => {
		stopPolling();
	});

	$effect(() => {
		if (hasProcessingDocuments) {
			startPolling();
		} else {
			stopPolling();
		}
	});

	function startPolling() {
		if (pollInterval) return;
		pollInterval = setInterval(async () => {
			await loadDocuments();
		}, 5000);
	}

	function stopPolling() {
		if (pollInterval) {
			clearInterval(pollInterval);
			pollInterval = null;
		}
	}

	async function loadDocuments() {
		try {
			const response = await documentsApi.list(1, 100);
			documents = response.items;
		} catch (e) {
			console.error('Failed to load documents:', e);
		} finally {
			loading = false;
		}
	}

	function handleUpload(document: Document) {
		documents = [document, ...documents];
	}

	async function handleDelete(id: string) {
		try {
			await documentsApi.delete(id);
			documents = documents.filter((doc) => doc.id !== id);
		} catch (e) {
			console.error('Failed to delete document:', e);
		}
	}

	function handleFilterChange(value: string | undefined) {
		if (value) {
			statusFilter = value as StatusFilter;
		}
	}

	function handleEdit(document: Document) {
		editingDocument = document;
		editDialogOpen = true;
	}

	function handleUpdate(updated: Document) {
		documents = documents.map((doc) =>
			doc.id === updated.id ? updated : doc
		);
	}
</script>

<svelte:head>
	<title>{m.documents_page_title()}</title>
</svelte:head>

<div class="flex h-full flex-col">
	<!-- Content -->
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-6xl">
			<!-- Header -->
			<div class="flex items-center justify-between mb-6">
				<div class="flex items-center gap-3">
					<FileText class="size-8 text-foreground" />
					<h1 class="text-3xl font-semibold text-foreground">{m.documents_title()}</h1>
				</div>
				{#if documents.length > 0}
					<span class="text-sm text-muted-foreground">{m.documents_count({ count: documents.length })}</span>
				{/if}
			</div>

			<!-- Search -->
			<div class="relative mb-6">
				<Search
					class="absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted-foreground"
				/>
				<Input
					type="search"
					placeholder={m.documents_search_placeholder()}
					class="pl-12 h-12 bg-white border-border rounded-lg text-base"
					bind:value={searchQuery}
				/>
			</div>

			<!-- Filter -->
			<div class="flex justify-end mb-4">
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<span>{m.common_filter_by()}</span>
					<Select.Root type="single" onValueChange={handleFilterChange}>
						<Select.Trigger class="w-32 h-8">
							<span>{filterOptions.find((o) => o.value === statusFilter)?.label || m.common_all()}</span>
						</Select.Trigger>
						<Select.Content align="end">
							{#each filterOptions as option}
								<Select.Item value={option.value}>{option.label}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
			</div>

			{#if loading}
				<div class="flex items-center justify-center py-12">
					<div
						class="size-8 animate-spin rounded-full border-4 border-muted border-t-primary"
					></div>
				</div>
			{:else}
				<!-- Document Grid -->
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
					<!-- Upload Card (first item) -->
					<DocumentUpload onUpload={handleUpload} />

					<!-- Document Cards -->
					{#each filteredDocuments() as document (document.id)}
						<DocumentCard {document} onDelete={handleDelete} onEdit={handleEdit} />
					{/each}
				</div>

				<!-- Empty state (when no documents match filter/search) -->
				{#if filteredDocuments().length === 0 && (searchQuery || statusFilter !== 'all')}
					<div class="mt-8 rounded-lg bg-white border border-border flex flex-col items-center p-12">
						<FileText class="size-12 text-muted-foreground/50" />
						<h3 class="mt-4 text-lg font-medium">{m.documents_no_documents()}</h3>
						<p class="mt-1 text-sm text-muted-foreground">
							{#if searchQuery}
								{m.documents_no_match({ query: searchQuery })}
							{:else}
								{m.documents_no_status({ status: statusFilter })}
							{/if}
						</p>
					</div>
				{/if}

				<!-- Processing indicator -->
				{#if hasProcessingDocuments}
					<p class="mt-4 text-center text-xs text-muted-foreground">
						{m.documents_auto_refresh()}
					</p>
				{/if}
			{/if}
		</div>
	</div>
</div>

<!-- Edit Document Dialog -->
{#if editingDocument}
	<DocumentEditDialog
		document={editingDocument}
		open={editDialogOpen}
		onOpenChange={(open) => {
			editDialogOpen = open;
			if (!open) editingDocument = null;
		}}
		onUpdate={handleUpdate}
	/>
{/if}
