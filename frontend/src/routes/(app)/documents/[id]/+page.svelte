<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { documentsApi, type DocumentDetail } from '$lib/api/documents';
	import PDFViewer from '$lib/components/pdf-viewer/PDFViewer.svelte';
	import DocumentChat from '$lib/components/pdf-viewer/DocumentChat.svelte';
	import { Button } from '$lib/components/ui/button';
	import { ArrowLeft, FileText, MessageSquare, PanelRightClose, PanelRight } from 'lucide-svelte';

	const API_BASE = import.meta.env.VITE_API_URL || '';

	let document = $state<DocumentDetail | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let showChat = $state(true);
	let chatPanelWidth = $state(500);
	let isResizing = $state(false);

	let documentId = $derived($page.params.id);
	let pdfUrl = $derived(document ? `${API_BASE}/documents/${document.id}/file` : '');
	let isPdf = $derived(document?.file_type === 'pdf');

	onMount(async () => {
		if (documentId) {
			await loadDocument();
		}
	});

	async function loadDocument() {
		if (!documentId) {
			error = 'Document ID is required';
			loading = false;
			return;
		}

		loading = true;
		error = null;

		try {
			document = await documentsApi.get(documentId);
		} catch (e) {
			console.error('Failed to load document:', e);
			error = e instanceof Error ? e.message : 'Failed to load document';
		} finally {
			loading = false;
		}
	}

	function goBack() {
		goto('/documents');
	}

	function toggleChat() {
		showChat = !showChat;
	}

	// Resizable panel handlers
	function startResize(e: MouseEvent) {
		isResizing = true;
		e.preventDefault();
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isResizing) return;
		const newWidth = window.innerWidth - e.clientX;
		chatPanelWidth = Math.max(350, Math.min(800, newWidth));
	}

	function stopResize() {
		isResizing = false;
	}
</script>

<svelte:window onmousemove={handleMouseMove} onmouseup={stopResize} />

<svelte:head>
	<title>{document?.filename || 'Document'} | RAG Agent</title>
</svelte:head>

<div class="flex h-full flex-col">
	<!-- Header -->
	<div class="shrink-0 border-b bg-background px-4 py-3">
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<Button variant="ghost" size="icon" onclick={goBack}>
					<ArrowLeft class="size-4" />
				</Button>
				<div class="flex items-center gap-2">
					<FileText class="size-5" />
					<h1 class="text-lg font-semibold truncate max-w-md">
						{document?.filename || 'Loading...'}
					</h1>
				</div>
			</div>

			<Button variant="outline" size="sm" onclick={toggleChat}>
				{#if showChat}
					<PanelRightClose class="mr-2 size-4" />
					Hide Chat
				{:else}
					<PanelRight class="mr-2 size-4" />
					Show Chat
				{/if}
			</Button>
		</div>
	</div>

	<!-- Content -->
	<div class="flex flex-1 overflow-hidden">
		{#if loading}
			<div class="flex flex-1 items-center justify-center">
				<div class="size-8 animate-spin rounded-full border-4 border-muted border-t-primary"></div>
			</div>
		{:else if error}
			<div class="flex flex-1 items-center justify-center">
				<div class="text-center">
					<p class="text-destructive">{error}</p>
					<Button variant="outline" class="mt-4" onclick={loadDocument}>
						Retry
					</Button>
				</div>
			</div>
		{:else if document}
			<!-- PDF/Document Viewer -->
			<div class="flex-1 overflow-hidden">
				{#if isPdf}
					<PDFViewer url={pdfUrl} />
				{:else}
					<!-- Non-PDF document view -->
					<div class="flex h-full items-center justify-center bg-muted/30">
						<div class="text-center">
							<FileText class="mx-auto size-16 text-muted-foreground/50" />
							<h2 class="mt-4 text-lg font-medium">{document.filename}</h2>
							<p class="mt-2 text-sm text-muted-foreground">
								Preview not available for {document.file_type.toUpperCase()} files
							</p>
							<p class="mt-1 text-xs text-muted-foreground">
								You can still chat about this document using the panel on the right.
							</p>
						</div>
					</div>
				{/if}
			</div>

			<!-- Chat Panel -->
			{#if showChat}
				<!-- Resize Handle -->
				<div
					class="w-1 cursor-col-resize bg-border hover:bg-primary/50 transition-colors"
					onmousedown={startResize}
					role="separator"
					aria-label="Resize chat panel"
				></div>

				<!-- Chat -->
				<div
					class="shrink-0 overflow-hidden border-l"
					style="width: {chatPanelWidth}px"
				>
					<DocumentChat
						documentId={document.id}
						documentName={document.filename}
					/>
				</div>
			{/if}
		{/if}
	</div>
</div>

<style>
	/* Prevent text selection while resizing */
	:global(body.resizing) {
		user-select: none;
		cursor: col-resize;
	}
</style>
