<script lang="ts">
	import { onMount } from 'svelte';
	import { Sparkles, Loader2 } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { imagesApi, type ImageModel, type ImageSize, type ImageHistoryItem } from '$lib/api';
	import {
		ImageLightbox,
		ImageGenerator,
		ImagePreview,
		ImageHistory,
		type ImageItem
	} from '$lib/components/images';

	// State
	let prompt = $state('');
	let generating = $state(false);
	let latestImage = $state<ImageItem | null>(null);
	let history = $state<ImageItem[]>([]);

	// Settings
	let selectedModel = $state('gemini/imagen-4.0-generate-001');
	let selectedSize = $state('1024x1024');

	// Available options from API
	let models = $state<ImageModel[]>([]);
	let sizes = $state<ImageSize[]>([]);
	let loading = $state(true);
	let historyTotal = $state(0);

	// Lightbox state
	let lightboxOpen = $state(false);
	let lightboxIndex = $state(0);

	// All images for lightbox navigation (latestImage + history)
	let allImages = $derived(latestImage ? [latestImage, ...history] : history);

	onMount(async () => {
		try {
			const [modelsRes, sizesRes, historyRes] = await Promise.all([
				imagesApi.getImageModels(),
				imagesApi.getImageSizes(),
				imagesApi.getImageHistory(50, 0)
			]);
			models = modelsRes.models;
			sizes = sizesRes.sizes;
			historyTotal = historyRes.total;

			// Load history from API
			history = historyRes.images.map((img: ImageHistoryItem) => ({
				id: img.id,
				url: img.image_url,
				prompt: img.prompt,
				model: img.model,
				size: img.size,
				createdAt: new Date(img.created_at)
			}));

			// Set default model if available
			if (models.length > 0) {
				selectedModel = models[0].id;
			}
		} catch (err) {
			console.error('Failed to load image options:', err);
			toast.error('Failed to load image generation options');
		} finally {
			loading = false;
		}
	});

	// Actions
	async function handleGenerate() {
		if (!prompt.trim() || generating) return;

		generating = true;

		try {
			const response = await imagesApi.generateImage({
				prompt: prompt.trim(),
				model: selectedModel,
				size: selectedSize,
				n: 1
			});

			if (response.images.length > 0) {
				const img = response.images[0];

				const newImage: ImageItem = {
					id: img.id,
					url: img.url,
					prompt: img.revised_prompt || prompt,
					model: response.model,
					size: response.size,
					createdAt: new Date(response.created)
				};

				// Add current latest to history
				if (latestImage) {
					history = [latestImage, ...history];
				}

				latestImage = newImage;
				historyTotal++;
				toast.success('Image generated successfully!');
			}
		} catch (err) {
			console.error('Image generation failed:', err);
			toast.error(err instanceof Error ? err.message : 'Failed to generate image');
		} finally {
			generating = false;
		}
	}

	function handleDownload() {
		if (!latestImage) return;

		if (latestImage.url.startsWith('data:')) {
			const link = document.createElement('a');
			link.href = latestImage.url;
			link.download = `generated-image-${latestImage.id}.png`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
		} else {
			window.open(latestImage.url, '_blank');
		}
	}

	async function handleDelete() {
		if (!latestImage) return;

		try {
			await imagesApi.deleteImage(latestImage.id);
			toast.success('Image deleted');

			// Move to next image from history or clear
			if (history.length > 0) {
				latestImage = history[0];
				history = history.slice(1);
			} else {
				latestImage = null;
			}
			historyTotal--;
		} catch (err) {
			console.error('Failed to delete image:', err);
			toast.error('Failed to delete image');
		}
	}

	async function handleDeleteFromHistory(image: ImageItem) {
		try {
			await imagesApi.deleteImage(image.id);
			history = history.filter((h) => h.id !== image.id);
			historyTotal--;
			toast.success('Image deleted');
		} catch (err) {
			console.error('Failed to delete image:', err);
			toast.error('Failed to delete image');
		}
	}

	// Lightbox functions
	function openLightboxForLatest() {
		lightboxIndex = 0;
		lightboxOpen = true;
	}

	function openLightboxForHistory(historyIndex: number) {
		// historyIndex is relative to history array, but allImages has latestImage at index 0
		lightboxIndex = latestImage ? historyIndex + 1 : historyIndex;
		lightboxOpen = true;
	}
</script>

<svelte:head>
	<title>Image Generation | RAG Agent</title>
</svelte:head>

<div class="flex h-full flex-col overflow-hidden">
	<!-- Main Content -->
	<div class="flex-1 overflow-auto">
		<div class="mx-auto max-w-7xl p-6">
			<!-- Header -->
			<div class="mb-6 flex items-center gap-3">
				<div class="flex size-10 items-center justify-center rounded-lg bg-primary/10">
					<Sparkles class="size-5 text-primary" />
				</div>
				<div>
					<h1 class="text-2xl font-semibold text-foreground">Image Generation</h1>
					<p class="text-sm text-muted-foreground">Create images with AI</p>
				</div>
			</div>

			{#if loading}
				<div class="flex items-center justify-center py-12">
					<Loader2 class="size-8 animate-spin text-primary" />
				</div>
			{:else}
				<!-- Two Column Layout -->
				<div class="grid gap-6 lg:grid-cols-2">
					<!-- Left Column: Input & Settings -->
					<ImageGenerator
						bind:prompt
						bind:selectedModel
						bind:selectedSize
						{models}
						{sizes}
						{generating}
						onGenerate={handleGenerate}
					/>

					<!-- Right Column: Latest Generated Image -->
					<ImagePreview
						image={latestImage}
						{generating}
						onOpenLightbox={openLightboxForLatest}
						onDownload={handleDownload}
						onDelete={handleDelete}
						onRegenerate={handleGenerate}
					/>
				</div>

				<!-- History Section -->
				<ImageHistory
					images={history}
					total={historyTotal}
					onImageClick={openLightboxForHistory}
					onImageDelete={handleDeleteFromHistory}
				/>
			{/if}
		</div>
	</div>
</div>

<!-- Lightbox -->
<ImageLightbox
	bind:open={lightboxOpen}
	bind:currentIndex={lightboxIndex}
	images={allImages}
/>
