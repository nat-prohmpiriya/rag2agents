<script lang="ts">
	import { onMount } from 'svelte';
	import { Image, Sparkles, Download, Save, RefreshCw, Loader2, Settings2 } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { Button } from '$lib/components/ui/button';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Label } from '$lib/components/ui/label';
	import * as Select from '$lib/components/ui/select';
	import { Separator } from '$lib/components/ui/separator';
	import { imagesApi, type ImageModel, type ImageSize } from '$lib/api';

	// State
	let prompt = $state('');
	let generating = $state(false);
	let latestImage = $state<{
		id: string;
		url: string;
		prompt: string;
		model: string;
		size: string;
		createdAt: Date;
	} | null>(null);

	let history = $state<
		Array<{
			id: string;
			url: string;
			prompt: string;
			model: string;
			size: string;
			createdAt: Date;
		}>
	>([]);

	// Settings
	let selectedModel = $state('gemini/imagen-4.0-generate-001');
	let selectedSize = $state('1024x1024');

	// Available options from API
	let models = $state<ImageModel[]>([]);
	let sizes = $state<ImageSize[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const [modelsRes, sizesRes] = await Promise.all([
				imagesApi.getImageModels(),
				imagesApi.getImageSizes()
			]);
			models = modelsRes.models;
			sizes = sizesRes.sizes;

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

				const newImage = {
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

		// Handle base64 data URL
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

	function handleSaveToKB() {
		if (!latestImage) return;
		toast.info('Save to Knowledge Base - Coming soon!');
	}

	function handleSelectFromHistory(image: (typeof history)[0]) {
		if (latestImage) {
			const current = latestImage;
			const existsInHistory = history.some((h) => h.id === current.id);
			if (!existsInHistory) {
				history = [current, ...history];
			}
		}
		history = history.filter((h) => h.id !== image.id);
		latestImage = image;
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
					<div class="flex flex-col gap-4">
						<!-- Prompt Input -->
						<div class="rounded-lg border bg-card p-4">
							<Label for="prompt" class="mb-2 block text-sm font-medium">Prompt</Label>
							<Textarea
								id="prompt"
								bind:value={prompt}
								placeholder="Describe the image you want to generate..."
								class="min-h-[120px] resize-none"
								disabled={generating}
							/>

							<!-- Settings -->
							<div class="mt-4 grid grid-cols-2 gap-3">
								<!-- Model -->
								<div>
									<Label class="mb-1.5 block text-xs text-muted-foreground">Model</Label>
									<Select.Root type="single" bind:value={selectedModel}>
										<Select.Trigger class="w-full">
											{models.find((m) => m.id === selectedModel)?.name || 'Select model'}
										</Select.Trigger>
										<Select.Content>
											{#each models as model}
												<Select.Item value={model.id}>{model.name}</Select.Item>
											{/each}
										</Select.Content>
									</Select.Root>
								</div>

								<!-- Size -->
								<div>
									<Label class="mb-1.5 block text-xs text-muted-foreground">Size</Label>
									<Select.Root type="single" bind:value={selectedSize}>
										<Select.Trigger class="w-full">
											{sizes.find((s) => s.value === selectedSize)?.label || 'Select size'}
										</Select.Trigger>
										<Select.Content>
											{#each sizes as size}
												<Select.Item value={size.value}>{size.label}</Select.Item>
											{/each}
										</Select.Content>
									</Select.Root>
								</div>
							</div>

							<!-- Generate Button -->
							<Button
								class="mt-4 w-full"
								size="lg"
								disabled={!prompt.trim() || generating}
								onclick={handleGenerate}
							>
								{#if generating}
									<Loader2 class="mr-2 size-4 animate-spin" />
									Generating...
								{:else}
									<Sparkles class="mr-2 size-4" />
									Generate Image
								{/if}
							</Button>
						</div>

						<!-- Tips -->
						<div class="rounded-lg border bg-muted/30 p-4">
							<h3 class="mb-2 text-sm font-medium flex items-center gap-2">
								<Settings2 class="size-4" />
								Tips
							</h3>
							<ul class="space-y-1 text-xs text-muted-foreground">
								<li>• Be specific and descriptive in your prompt</li>
								<li>• Include style references (e.g., "oil painting", "3D render")</li>
								<li>• Mention lighting, mood, and composition</li>
								<li>• Use negative prompts to exclude unwanted elements</li>
							</ul>
						</div>
					</div>

					<!-- Right Column: Latest Generated Image -->
					<div class="flex flex-col gap-4">
						<div class="rounded-lg border bg-card p-4">
							<Label class="mb-3 block text-sm font-medium">Generated Image</Label>

							{#if generating}
								<!-- Loading State -->
								<div
									class="flex aspect-square items-center justify-center rounded-lg border-2 border-dashed bg-muted/30"
								>
									<div class="text-center">
										<Loader2 class="mx-auto size-12 animate-spin text-primary" />
										<p class="mt-4 text-sm text-muted-foreground">Generating your image...</p>
										<p class="mt-1 text-xs text-muted-foreground">This may take a few seconds</p>
									</div>
								</div>
							{:else if latestImage}
								<!-- Image Display -->
								<div class="overflow-hidden rounded-lg border">
									<img
										src={latestImage.url}
										alt={latestImage.prompt}
										class="aspect-square w-full object-cover"
									/>
								</div>

								<!-- Image Info -->
								<div class="mt-3 space-y-2">
									<p class="line-clamp-2 text-sm text-muted-foreground">
										"{latestImage.prompt}"
									</p>
									<div class="flex items-center gap-2 text-xs text-muted-foreground">
										<span class="rounded bg-muted px-1.5 py-0.5">{latestImage.model}</span>
										<span class="rounded bg-muted px-1.5 py-0.5">{latestImage.size}</span>
									</div>
								</div>

								<!-- Action Buttons -->
								<div class="mt-4 flex gap-2">
									<Button variant="outline" size="sm" class="flex-1" onclick={handleDownload}>
										<Download class="mr-2 size-4" />
										Download
									</Button>
									<Button variant="outline" size="sm" class="flex-1" onclick={handleSaveToKB}>
										<Save class="mr-2 size-4" />
										Save to KB
									</Button>
									<Button variant="outline" size="sm" onclick={handleGenerate} disabled={generating}>
										<RefreshCw class="size-4" />
									</Button>
								</div>
							{:else}
								<!-- Empty State -->
								<div
									class="flex aspect-square items-center justify-center rounded-lg border-2 border-dashed bg-muted/30"
								>
									<div class="text-center">
										<Image class="mx-auto size-12 text-muted-foreground/50" />
										<p class="mt-4 text-sm text-muted-foreground">No image generated yet</p>
										<p class="mt-1 text-xs text-muted-foreground">
											Enter a prompt and click Generate
										</p>
									</div>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- History Section -->
				{#if history.length > 0}
					<Separator class="my-8" />

					<div>
						<div class="mb-4 flex items-center justify-between">
							<h2 class="text-lg font-medium">History</h2>
							<span class="text-sm text-muted-foreground">{history.length} images</span>
						</div>

						<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
							{#each history as image (image.id)}
								<button
									type="button"
									class="group relative aspect-square overflow-hidden rounded-lg border bg-card transition-all hover:ring-2 hover:ring-primary"
									onclick={() => handleSelectFromHistory(image)}
								>
									<img src={image.url} alt={image.prompt} class="size-full object-cover" />
									<div
										class="absolute inset-0 flex items-end bg-linear-to-t from-black/60 to-transparent opacity-0 transition-opacity group-hover:opacity-100"
									>
										<p class="line-clamp-2 p-2 text-xs text-white">{image.prompt}</p>
									</div>
								</button>
							{/each}
						</div>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
