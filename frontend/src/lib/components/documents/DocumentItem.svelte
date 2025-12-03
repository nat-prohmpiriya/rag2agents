<script lang="ts">
	import { goto } from '$app/navigation';
	import { FileText, FileSpreadsheet, File, Trash2, ExternalLink } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import type { Document, DocumentStatus } from '$lib/api/documents';

	interface Props {
		document: Document;
		onDelete: (id: string) => void;
	}

	let { document, onDelete }: Props = $props();

	let showConfirm = $state(false);
	let isClickable = $derived(document.status === 'ready');

	function getStatusVariant(status: DocumentStatus): 'default' | 'secondary' | 'destructive' | 'outline' {
		switch (status) {
			case 'ready':
				return 'default';
			case 'processing':
			case 'pending':
				return 'secondary';
			case 'error':
				return 'destructive';
			default:
				return 'outline';
		}
	}

	function getStatusLabel(status: DocumentStatus): string {
		switch (status) {
			case 'ready':
				return 'Ready';
			case 'processing':
				return 'Processing';
			case 'pending':
				return 'Pending';
			case 'error':
				return 'Error';
			default:
				return status;
		}
	}

	function formatFileSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	function handleDeleteClick() {
		showConfirm = true;
	}

	function handleConfirmDelete() {
		onDelete(document.id);
		showConfirm = false;
	}

	function handleCancelDelete() {
		showConfirm = false;
	}

	function handleClick() {
		if (isClickable) {
			goto(`/documents/${document.id}`);
		}
	}

</script>

<div
	class="flex items-center gap-3 rounded-lg border bg-card p-3 transition-colors {isClickable ? 'cursor-pointer hover:bg-muted/50 hover:border-primary/50' : 'hover:bg-muted/30'}"
	onclick={handleClick}
	onkeydown={(e) => e.key === 'Enter' && handleClick()}
	role={isClickable ? 'button' : undefined}
	tabindex={isClickable ? 0 : undefined}
>
	<!-- File Icon -->
	<div class="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
		{#if document.file_type.toLowerCase().includes('pdf')}
			<FileText class="size-5 text-muted-foreground" />
		{:else if document.file_type.toLowerCase().includes('csv') || document.file_type.toLowerCase().includes('spreadsheet')}
			<FileSpreadsheet class="size-5 text-muted-foreground" />
		{:else}
			<File class="size-5 text-muted-foreground" />
		{/if}
	</div>

	<!-- File Info -->
	<div class="min-w-0 flex-1">
		<p class="truncate text-sm font-medium" title={document.filename}>
			{document.filename}
		</p>
		<div class="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
			<span>{formatFileSize(document.file_size)}</span>
			{#if document.chunk_count > 0}
				<span>&middot;</span>
				<span>{document.chunk_count} chunks</span>
			{/if}
		</div>
	</div>

	<!-- Status Badge -->
	<Badge variant={getStatusVariant(document.status)} class="shrink-0">
		{getStatusLabel(document.status)}
	</Badge>

	<!-- Actions -->
	<div class="flex items-center gap-1" onclick={(e) => e.stopPropagation()}>
		{#if isClickable}
			<Button
				variant="ghost"
				size="icon-sm"
				onclick={() => goto(`/documents/${document.id}`)}
				title="View document"
				class="shrink-0 text-muted-foreground hover:text-primary"
			>
				<ExternalLink class="size-4" />
			</Button>
		{/if}

		{#if showConfirm}
			<div class="flex items-center gap-1">
				<Button variant="destructive" size="sm" onclick={handleConfirmDelete}>
					Delete
				</Button>
				<Button variant="outline" size="sm" onclick={handleCancelDelete}>
					Cancel
				</Button>
			</div>
		{:else}
			<Button
				variant="ghost"
				size="icon-sm"
				onclick={handleDeleteClick}
				title="Delete document"
				class="shrink-0 text-muted-foreground hover:text-destructive"
			>
				<Trash2 class="size-4" />
			</Button>
		{/if}
	</div>
</div>
