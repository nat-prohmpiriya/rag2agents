<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as pdfjsLib from 'pdfjs-dist';
	import { ZoomIn, ZoomOut, ChevronLeft, ChevronRight, RotateCw } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';

	interface Props {
		url: string;
		onPageChange?: (page: number, totalPages: number) => void;
	}

	let { url, onPageChange }: Props = $props();

	// Get auth token for PDF fetch
	function getAuthHeaders(): Record<string, string> {
		const token = localStorage.getItem('access_token');
		return token ? { Authorization: `Bearer ${token}` } : {};
	}

	// PDF state
	let pdfDoc = $state<pdfjsLib.PDFDocumentProxy | null>(null);
	let currentPage = $state(1);
	let totalPages = $state(0);
	let scale = $state(1.0);
	let rotation = $state(0);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let pageInputValue = $state('1');

	// Canvas refs
	let mainCanvas = $state<HTMLCanvasElement | null>(null);
	let thumbnailContainer = $state<HTMLDivElement | null>(null);
	let thumbnails = $state<{ page: number; canvas: HTMLCanvasElement }[]>([]);

	// Zoom levels
	const MIN_SCALE = 0.5;
	const MAX_SCALE = 3.0;
	const SCALE_STEP = 0.25;

	// Set worker source
	onMount(async () => {
		// Configure PDF.js worker - use local worker from static folder
		pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
		await loadPDF();
	});

	onDestroy(() => {
		if (pdfDoc) {
			pdfDoc.destroy();
		}
	});

	async function loadPDF() {
		loading = true;
		error = null;

		try {
			// Create loading task with auth headers
			const loadingTask = pdfjsLib.getDocument({
				url,
				httpHeaders: getAuthHeaders(),
				withCredentials: false,
			});
			pdfDoc = await loadingTask.promise;
			totalPages = pdfDoc.numPages;
			pageInputValue = '1';

			// Render first page
			await renderPage(1);

			// Generate thumbnails
			await generateThumbnails();

			onPageChange?.(1, totalPages);
		} catch (e) {
			console.error('Failed to load PDF:', e);
			error = e instanceof Error ? e.message : 'Failed to load PDF';
		} finally {
			loading = false;
		}
	}

	async function renderPage(pageNum: number) {
		if (!pdfDoc || !mainCanvas) return;

		const page = await pdfDoc.getPage(pageNum);
		const viewport = page.getViewport({ scale, rotation });

		const context = mainCanvas.getContext('2d');
		if (!context) return;

		mainCanvas.height = viewport.height;
		mainCanvas.width = viewport.width;

		await page.render({
			canvasContext: context,
			viewport,
			canvas: mainCanvas,
		}).promise;
	}

	async function generateThumbnails() {
		if (!pdfDoc) return;

		const thumbScale = 0.2;
		const newThumbnails: { page: number; canvas: HTMLCanvasElement }[] = [];

		for (let i = 1; i <= totalPages; i++) {
			const page = await pdfDoc.getPage(i);
			const viewport = page.getViewport({ scale: thumbScale });

			const canvas = document.createElement('canvas');
			const context = canvas.getContext('2d');
			if (!context) continue;

			canvas.height = viewport.height;
			canvas.width = viewport.width;

			await page.render({
				canvasContext: context,
				viewport,
				canvas,
			}).promise;

			newThumbnails.push({ page: i, canvas });
		}

		thumbnails = newThumbnails;
	}

	function goToPage(pageNum: number) {
		if (pageNum < 1 || pageNum > totalPages) return;
		currentPage = pageNum;
		pageInputValue = String(pageNum);
		renderPage(pageNum);
		onPageChange?.(pageNum, totalPages);
	}

	function nextPage() {
		if (currentPage < totalPages) {
			goToPage(currentPage + 1);
		}
	}

	function prevPage() {
		if (currentPage > 1) {
			goToPage(currentPage - 1);
		}
	}

	function zoomIn() {
		if (scale < MAX_SCALE) {
			scale = Math.min(scale + SCALE_STEP, MAX_SCALE);
			renderPage(currentPage);
		}
	}

	function zoomOut() {
		if (scale > MIN_SCALE) {
			scale = Math.max(scale - SCALE_STEP, MIN_SCALE);
			renderPage(currentPage);
		}
	}

	function rotate() {
		rotation = (rotation + 90) % 360;
		renderPage(currentPage);
	}

	function handlePageInput(e: Event) {
		const target = e.target as HTMLInputElement;
		const value = parseInt(target.value, 10);
		if (!isNaN(value) && value >= 1 && value <= totalPages) {
			goToPage(value);
		}
	}

	function handleThumbnailClick(pageNum: number) {
		goToPage(pageNum);
	}

	// Re-render when scale or rotation changes
	$effect(() => {
		if (pdfDoc && mainCanvas) {
			renderPage(currentPage);
		}
	});

	// Reload when URL changes
	$effect(() => {
		if (url) {
			loadPDF();
		}
	});
</script>

<div class="flex h-full bg-muted/30">
	<!-- Thumbnails Sidebar -->
	<div
		bind:this={thumbnailContainer}
		class="w-32 shrink-0 overflow-y-auto border-r bg-background p-2 hidden md:block"
	>
		<div class="space-y-2">
			{#each thumbnails as thumb (thumb.page)}
				<button
					onclick={() => handleThumbnailClick(thumb.page)}
					class="relative block w-full rounded border-2 transition-colors {currentPage === thumb.page
						? 'border-primary'
						: 'border-transparent hover:border-muted-foreground/30'}"
				>
					<img
						src={thumb.canvas.toDataURL()}
						alt="Page {thumb.page}"
						class="w-full"
					/>
					<span
						class="absolute bottom-1 left-1/2 -translate-x-1/2 rounded bg-background/80 px-1.5 py-0.5 text-xs font-medium"
					>
						{thumb.page}
					</span>
				</button>
			{/each}
		</div>
	</div>

	<!-- Main Content -->
	<div class="flex flex-1 flex-col overflow-hidden">
		<!-- Toolbar -->
		<div class="flex items-center justify-between border-b bg-background px-4 py-2">
			<div class="flex items-center gap-2">
				<Button variant="ghost" size="icon" onclick={prevPage} disabled={currentPage <= 1}>
					<ChevronLeft class="size-4" />
				</Button>
				<div class="flex items-center gap-1">
					<Input
						type="number"
						class="h-8 w-16 text-center"
						bind:value={pageInputValue}
						onchange={handlePageInput}
						min="1"
						max={totalPages}
					/>
					<span class="text-sm text-muted-foreground">/ {totalPages}</span>
				</div>
				<Button variant="ghost" size="icon" onclick={nextPage} disabled={currentPage >= totalPages}>
					<ChevronRight class="size-4" />
				</Button>
			</div>

			<div class="flex items-center gap-2">
				<Button variant="ghost" size="icon" onclick={zoomOut} disabled={scale <= MIN_SCALE}>
					<ZoomOut class="size-4" />
				</Button>
				<span class="min-w-12 text-center text-sm">{Math.round(scale * 100)}%</span>
				<Button variant="ghost" size="icon" onclick={zoomIn} disabled={scale >= MAX_SCALE}>
					<ZoomIn class="size-4" />
				</Button>
				<Button variant="ghost" size="icon" onclick={rotate}>
					<RotateCw class="size-4" />
				</Button>
			</div>
		</div>

		<!-- PDF Canvas Area -->
		<div class="flex-1 overflow-auto p-4">
			{#if loading}
				<div class="flex h-full items-center justify-center">
					<div class="size-8 animate-spin rounded-full border-4 border-muted border-t-primary"></div>
				</div>
			{:else if error}
				<div class="flex h-full items-center justify-center">
					<div class="text-center">
						<p class="text-destructive">{error}</p>
						<Button variant="outline" class="mt-4" onclick={loadPDF}>
							Retry
						</Button>
					</div>
				</div>
			{:else}
				<div class="flex justify-center">
					<canvas
						bind:this={mainCanvas}
						class="shadow-lg"
					></canvas>
				</div>
			{/if}
		</div>
	</div>
</div>
