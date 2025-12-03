<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { ScrollArea } from '$lib/components/ui/scroll-area';
	import { FolderOpen, Plus, FileText } from 'lucide-svelte';
	import type { Project } from '$lib/api';

	let {
		projects = [],
		currentProjectId = null,
		loading = false,
		onSelect,
		onCreate
	} = $props<{
		projects: Project[];
		currentProjectId: string | null;
		loading?: boolean;
		onSelect: (id: string | null) => void;
		onCreate: () => void;
	}>();

	let isAllSelected = $derived(currentProjectId === null);
</script>

<div class="flex flex-col gap-2">
	<!-- Header with title and add button -->
	<div class="flex items-center justify-between px-1">
		<span class="text-sm font-medium text-muted-foreground">Projects</span>
		<Button variant="ghost" size="icon" class="h-6 w-6" onclick={onCreate} disabled={loading}>
			<Plus class="h-4 w-4" />
		</Button>
	</div>

	<!-- All Documents option -->
	<Button
		variant={isAllSelected ? 'secondary' : 'ghost'}
		class="w-full justify-start gap-2"
		onclick={() => onSelect(null)}
		disabled={loading}
	>
		<FileText class="h-4 w-4" />
		<span class="truncate">All Documents</span>
	</Button>

	<!-- Project list -->
	{#if projects.length > 0}
		<ScrollArea class="max-h-48">
			<div class="flex flex-col gap-1">
				{#each projects as project (project.id)}
					{@const isSelected = currentProjectId === project.id}
					<Button
						variant={isSelected ? 'secondary' : 'ghost'}
						class="w-full justify-start gap-2"
						onclick={() => onSelect(project.id)}
						disabled={loading}
					>
						<FolderOpen class="h-4 w-4 flex-shrink-0" />
						<span class="truncate">{project.name}</span>
					</Button>
				{/each}
			</div>
		</ScrollArea>
	{:else if !loading}
		<p class="px-2 py-1 text-xs text-muted-foreground">No projects yet</p>
	{/if}

	{#if loading}
		<p class="px-2 py-1 text-xs text-muted-foreground">Loading...</p>
	{/if}
</div>
