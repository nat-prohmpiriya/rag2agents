<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth, projectStore } from '$lib/stores';
	import { getUserDisplayName } from '$lib/types';
	import AppLayout from '$lib/components/layout/AppLayout.svelte';
	import ProjectDialog from '$lib/components/projects/ProjectDialog.svelte';
	import type { ProjectCreate, ProjectUpdate } from '$lib/api';

	let { children }: { children: Snippet } = $props();

	// Project dialog state
	let showProjectDialog = $state(false);

	// Auth guard - redirect to login if not authenticated
	$effect(() => {
		if (!auth.isLoading && !auth.isAuthenticated) {
			goto('/login');
		}
	});

	// Initialize and load projects on mount
	onMount(() => {
		if (auth.isAuthenticated) {
			projectStore.initialize();
			projectStore.loadProjects();
		}
	});

	function handleLogout() {
		projectStore.clear();
		auth.logout();
		goto('/login');
	}

	function handleNewProject() {
		showProjectDialog = true;
	}

	function handleProjectSelect(projectId: string | null) {
		projectStore.selectProject(projectId);
	}

	async function handleProjectSave(data: ProjectCreate | ProjectUpdate) {
		try {
			const project = await projectStore.createProject(data as ProjectCreate);
			projectStore.selectProject(project.id);
			showProjectDialog = false;
		} catch (e) {
			console.error('Failed to create project:', e);
		}
	}
</script>

{#if auth.isLoading}
	<div class="min-h-screen flex items-center justify-center bg-background">
		<div class="flex flex-col items-center gap-4">
			<svg class="h-8 w-8 animate-spin text-primary" viewBox="0 0 24 24">
				<circle
					class="opacity-25"
					cx="12"
					cy="12"
					r="10"
					stroke="currentColor"
					stroke-width="4"
					fill="none"
				/>
				<path
					class="opacity-75"
					fill="currentColor"
					d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
				/>
			</svg>
			<p class="text-muted-foreground">Loading...</p>
		</div>
	</div>
{:else if auth.isAuthenticated}
	<AppLayout
		user={auth.user ? { name: getUserDisplayName(auth.user), email: auth.user.email } : null}
		currentProject={projectStore.currentProject}
		currentProjectId={projectStore.currentProjectId}
		projects={projectStore.projects}
		loading={projectStore.loading}
		onLogout={handleLogout}
		onNewProject={handleNewProject}
		onProjectSelect={handleProjectSelect}
	>
		{@render children()}
	</AppLayout>

	<!-- Create Project Dialog -->
	<ProjectDialog
		bind:open={showProjectDialog}
		project={null}
		onSave={handleProjectSave}
	/>
{/if}
