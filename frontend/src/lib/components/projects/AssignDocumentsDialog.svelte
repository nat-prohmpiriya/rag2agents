<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { ScrollArea } from '$lib/components/ui/scroll-area';
	import { Label } from '$lib/components/ui/label';
	import { documentsApi, type Document } from '$lib/api';
	import { FileText } from 'lucide-svelte';

	let {
		open = $bindable(false),
		projectId,
		existingDocumentIds = [],
		onAssign
	} = $props<{
		open: boolean;
		projectId: string;
		existingDocumentIds: string[];
		onAssign: (documentIds: string[]) => Promise<void>;
	}>();

	let allDocuments = $state<Document[]>([]);
	let selectedIds = $state<Set<string>>(new Set());
	let loading = $state(false);
	let saving = $state(false);
	let error = $state<string | null>(null);

	// Filter to only show documents not already assigned
	let availableDocuments = $derived(
		allDocuments.filter((doc) => !existingDocumentIds.includes(doc.id))
	);

	let hasSelection = $derived(selectedIds.size > 0);

	// Load documents when dialog opens
	$effect(() => {
		if (open) {
			loadDocuments();
			selectedIds = new Set();
			error = null;
		}
	});

	async function loadDocuments() {
		loading = true;
		try {
			const response = await documentsApi.list(1, 100);
			allDocuments = response.items;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load documents';
			allDocuments = [];
		} finally {
			loading = false;
		}
	}

	function toggleDocument(docId: string, checked: boolean) {
		const newSet = new Set(selectedIds);
		if (checked) {
			newSet.add(docId);
		} else {
			newSet.delete(docId);
		}
		selectedIds = newSet;
	}

	function selectAll() {
		selectedIds = new Set(availableDocuments.map((d) => d.id));
	}

	function deselectAll() {
		selectedIds = new Set();
	}

	async function handleAssign() {
		if (!hasSelection || saving) return;

		saving = true;
		error = null;

		try {
			await onAssign(Array.from(selectedIds));
			open = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to assign documents';
		} finally {
			saving = false;
		}
	}

	function handleClose() {
		if (!saving) {
			open = false;
		}
	}

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}
</script>

<Dialog.Root bind:open onOpenChange={(isOpen) => !isOpen && handleClose()}>
	<Dialog.Portal>
		<Dialog.Overlay />
		<Dialog.Content class="sm:max-w-lg">
			<Dialog.Header>
				<Dialog.Title>Assign Documents</Dialog.Title>
				<Dialog.Description>
					Select documents to add to this project. Only documents not already in the project are
					shown.
				</Dialog.Description>
			</Dialog.Header>

			{#if loading}
				<div class="flex items-center justify-center py-8">
					<p class="text-sm text-muted-foreground">Loading documents...</p>
				</div>
			{:else if availableDocuments.length === 0}
				<div class="flex flex-col items-center justify-center py-8 text-center">
					<FileText class="mb-2 h-8 w-8 text-muted-foreground" />
					<p class="text-sm text-muted-foreground">
						{allDocuments.length === 0
							? 'No documents uploaded yet'
							: 'All documents are already assigned to this project'}
					</p>
				</div>
			{:else}
				<!-- Select all / Deselect all -->
				<div class="mb-2 flex items-center justify-between">
					<span class="text-sm text-muted-foreground">
						{selectedIds.size} of {availableDocuments.length} selected
					</span>
					<div class="flex gap-2">
						<Button variant="ghost" size="sm" onclick={selectAll} disabled={saving}>
							Select All
						</Button>
						<Button
							variant="ghost"
							size="sm"
							onclick={deselectAll}
							disabled={saving || !hasSelection}
						>
							Clear
						</Button>
					</div>
				</div>

				<ScrollArea class="h-64 rounded border">
					<div class="space-y-1 p-2">
						{#each availableDocuments as doc (doc.id)}
							{@const isChecked = selectedIds.has(doc.id)}
							<label
								class="flex cursor-pointer items-center gap-3 rounded-lg p-2 transition-colors hover:bg-accent"
							>
								<Checkbox
									checked={isChecked}
									onCheckedChange={(checked) => toggleDocument(doc.id, checked === true)}
									disabled={saving}
								/>
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium">{doc.filename}</p>
									<p class="text-xs text-muted-foreground">
										{doc.file_type} &bull; {formatFileSize(doc.file_size)}
									</p>
								</div>
							</label>
						{/each}
					</div>
				</ScrollArea>
			{/if}

			{#if error}
				<p class="text-sm text-destructive">{error}</p>
			{/if}

			<Dialog.Footer>
				<Button variant="outline" onclick={handleClose} disabled={saving}>Cancel</Button>
				<Button
					onclick={handleAssign}
					disabled={!hasSelection || saving || loading}
				>
					{#if saving}
						Assigning...
					{:else}
						Assign {selectedIds.size > 0 ? `(${selectedIds.size})` : ''}
					{/if}
				</Button>
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
