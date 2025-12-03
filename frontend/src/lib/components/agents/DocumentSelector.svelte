<script lang="ts">
	import { onMount } from 'svelte';
	import { FileText, Search, Loader2 } from 'lucide-svelte';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { Input } from '$lib/components/ui/input';
	import { Badge } from '$lib/components/ui/badge';
	import { Label } from '$lib/components/ui/label';
	import { documentsApi, type Document, type DocumentStatus } from '$lib/api';

	interface Props {
		selectedIds: string[];
		onChange: (ids: string[]) => void;
	}

	let { selectedIds, onChange }: Props = $props();

	let documents = $state<Document[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let searchQuery = $state('');

	// Filtered documents based on search
	let filteredDocuments = $derived(
		documents.filter(doc =>
			doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
		)
	);

	onMount(async () => {
		await loadDocuments();
	});

	async function loadDocuments() {
		loading = true;
		error = null;
		try {
			// Load all documents (up to 100)
			const response = await documentsApi.list(1, 100);
			documents = response.items;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load documents';
		} finally {
			loading = false;
		}
	}

	function isSelected(docId: string): boolean {
		return selectedIds.includes(docId);
	}

	function toggleDocument(docId: string) {
		if (isSelected(docId)) {
			onChange(selectedIds.filter(id => id !== docId));
		} else {
			onChange([...selectedIds, docId]);
		}
	}

	function getStatusColor(status: DocumentStatus): string {
		switch (status) {
			case 'ready': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
			case 'processing': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
			case 'pending': return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
			case 'error': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
			default: return '';
		}
	}

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function getFileTypeIcon(fileType: string): string {
		if (fileType.includes('pdf')) return 'PDF';
		if (fileType.includes('word') || fileType.includes('doc')) return 'DOC';
		if (fileType.includes('text') || fileType.includes('txt')) return 'TXT';
		if (fileType.includes('markdown') || fileType.includes('md')) return 'MD';
		return 'FILE';
	}
</script>

<div class="space-y-3">
	<!-- Search -->
	<div class="relative">
		<Search class="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
		<Input
			type="text"
			placeholder="Search documents..."
			bind:value={searchQuery}
			class="pl-9"
		/>
	</div>

	<!-- Documents List -->
	<div class="border rounded-lg max-h-64 overflow-y-auto">
		{#if loading}
			<div class="flex items-center justify-center py-8">
				<Loader2 class="size-5 animate-spin text-muted-foreground" />
				<span class="ml-2 text-sm text-muted-foreground">Loading documents...</span>
			</div>
		{:else if error}
			<div class="p-4 text-center text-destructive text-sm">
				{error}
			</div>
		{:else if documents.length === 0}
			<div class="p-4 text-center text-muted-foreground text-sm">
				<FileText class="size-8 mx-auto mb-2 opacity-50" />
				No documents available. Upload documents first.
			</div>
		{:else if filteredDocuments.length === 0}
			<div class="p-4 text-center text-muted-foreground text-sm">
				No documents match your search.
			</div>
		{:else}
			<div class="divide-y">
				{#each filteredDocuments as doc (doc.id)}
					<button
						type="button"
						class="w-full flex items-center gap-3 p-3 hover:bg-muted/50 transition-colors text-left"
						onclick={() => toggleDocument(doc.id)}
					>
						<Checkbox
							checked={isSelected(doc.id)}
							onCheckedChange={() => toggleDocument(doc.id)}
						/>
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2">
								<span class="text-sm font-medium truncate">{doc.filename}</span>
								<Badge variant="outline" class="text-xs shrink-0">
									{getFileTypeIcon(doc.file_type)}
								</Badge>
							</div>
							<div class="flex items-center gap-2 mt-1">
								<span class="text-xs text-muted-foreground">
									{formatFileSize(doc.file_size)}
								</span>
								<span class="text-muted-foreground">·</span>
								<span class="text-xs text-muted-foreground">
									{doc.chunk_count} chunks
								</span>
								<Badge class={`text-xs ${getStatusColor(doc.status)}`}>
									{doc.status}
								</Badge>
							</div>
						</div>
					</button>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Selection Info -->
	{#if selectedIds.length > 0}
		<p class="text-xs text-muted-foreground">
			{selectedIds.length} document{selectedIds.length > 1 ? 's' : ''} selected
		</p>
	{/if}
</div>
