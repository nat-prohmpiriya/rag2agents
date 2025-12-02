<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import * as Sheet from '$lib/components/ui/sheet';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import Header from './Header.svelte';
	import Sidebar from './Sidebar.svelte';
	import { Menu } from 'lucide-svelte';
	import { sidebar } from '$lib/stores';

	let { children, user, currentProject, projects, onLogout, onProjectSelect, onNewProject }: {
		children?: Snippet;
		user?: { name: string; email: string; avatar?: string } | null;
		currentProject?: { id: string; name: string } | null;
		projects?: { id: string; name: string }[];
		onLogout?: () => void;
		onProjectSelect?: (projectId: string) => void;
		onNewProject?: () => void;
	} = $props();

	let sidebarOpen = $state(false);

	onMount(() => {
		sidebar.initialize();
	});

	function handleToggle() {
		sidebar.toggle();
	}
</script>

<Tooltip.Provider>
	<div class="min-h-screen bg-background">
		<!-- Header -->
		<Header {user} {onLogout}>
			{#snippet sidebarTrigger()}
				<Sheet.Root bind:open={sidebarOpen}>
					<Sheet.Trigger>
						{#snippet child({ props })}
							<button
								{...props}
								class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-9 px-2 md:hidden"
							>
								<Menu class="h-5 w-5" />
								<span class="sr-only">Toggle sidebar</span>
							</button>
						{/snippet}
					</Sheet.Trigger>
					<Sheet.Content side="left" class="w-64 p-0">
						<Sidebar {currentProject} {projects} {onProjectSelect} {onNewProject} />
					</Sheet.Content>
				</Sheet.Root>
			{/snippet}
		</Header>

		<div class="flex">
			<!-- Desktop sidebar -->
			<div class="hidden md:block">
				<div class="sticky top-14 h-[calc(100vh-3.5rem)]">
					<Sidebar
						{currentProject}
						{projects}
						{onProjectSelect}
						{onNewProject}
						collapsed={sidebar.collapsed}
						onToggle={handleToggle}
					/>
				</div>
			</div>

			<!-- Main content -->
			<main class="flex-1 min-w-0">
				{#if children}
					{@render children()}
				{/if}
			</main>
		</div>
	</div>
</Tooltip.Provider>
