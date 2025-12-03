<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button';
	import { ScrollArea } from '$lib/components/ui/scroll-area';
	import { Separator } from '$lib/components/ui/separator';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Avatar from '$lib/components/ui/avatar';
	import { MessageSquare, FileText, Bot, ChevronLeft, ChevronRight, FolderOpen, LogOut, User, Settings } from 'lucide-svelte';
	import ProjectList from '$lib/components/projects/ProjectList.svelte';
	import type { Project } from '$lib/api';

	let {
		currentProject,
		projects = [],
		currentProjectId = null,
		loading = false,
		onProjectSelect,
		onNewProject,
		collapsed = false,
		onToggle,
		user,
		onLogout
	} = $props<{
		currentProject?: { id: string; name: string } | null;
		projects?: Project[];
		currentProjectId?: string | null;
		loading?: boolean;
		onProjectSelect?: (projectId: string | null) => void;
		onNewProject?: () => void;
		collapsed?: boolean;
		onToggle?: () => void;
		user?: { name: string; email: string; avatar?: string } | null;
		onLogout?: () => void;
	}>();

	interface NavItem {
		label: string;
		href: string;
		icon: typeof MessageSquare;
	}

	const navItems: NavItem[] = [
		{ label: 'Chat', href: '/chat', icon: MessageSquare },
		{ label: 'Documents', href: '/documents', icon: FileText },
		{ label: 'Agents', href: '/agents', icon: Bot }
	];

	function isActive(href: string): boolean {
		return $page.url.pathname.startsWith(href);
	}

	function handleProjectSelect(id: string | null) {
		onProjectSelect?.(id);
	}
</script>

<aside class="flex h-full flex-col border-r bg-background transition-all duration-300 {collapsed ? 'w-16' : 'w-64'}">
	<!-- Logo & Platform Name -->
	{#if !collapsed}
		<div class="flex items-center gap-2 p-4">
			<svg class="h-6 w-6 text-primary" viewBox="0 0 24 24" fill="currentColor">
				<path
					d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
					stroke="currentColor"
					stroke-width="2"
					fill="none"
				/>
			</svg>
			<span class="font-semibold">RAG Agent Platform</span>
		</div>
	{:else}
		<div class="flex justify-center p-4">
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<div {...props}>
							<svg class="h-6 w-6 text-primary" viewBox="0 0 24 24" fill="currentColor">
								<path
									d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
									stroke="currentColor"
									stroke-width="2"
									fill="none"
								/>
							</svg>
						</div>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Portal>
					<Tooltip.Content side="right">
						RAG Agent Platform
					</Tooltip.Content>
				</Tooltip.Portal>
			</Tooltip.Root>
		</div>
	{/if}
	<Separator />

	<!-- Project selector -->
	{#if !collapsed}
		<div class="p-4">
			<ProjectList
				{projects}
				{currentProjectId}
				{loading}
				onSelect={handleProjectSelect}
				onCreate={onNewProject ?? (() => {})}
			/>
		</div>
		<Separator />
	{:else}
		<div class="flex justify-center p-4">
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<Button {...props} variant="ghost" size="icon" onclick={onNewProject}>
							<FolderOpen class="h-5 w-5" />
						</Button>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Portal>
					<Tooltip.Content side="right">
						{currentProject?.name || 'Select project'}
					</Tooltip.Content>
				</Tooltip.Portal>
			</Tooltip.Root>
		</div>
		<Separator />
	{/if}

	<!-- Navigation -->
	<ScrollArea class="flex-1 px-2 py-4">
		<nav class="flex flex-col gap-1">
			{#each navItems as item}
				{@const Icon = item.icon}
				{#if collapsed}
					<Tooltip.Root>
						<Tooltip.Trigger>
							{#snippet child({ props })}
								<a
									{...props}
									href={item.href}
									class="flex items-center justify-center rounded-lg p-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground {isActive(item.href) ? 'bg-accent text-accent-foreground' : ''}"
								>
									<Icon class="h-5 w-5" />
								</a>
							{/snippet}
						</Tooltip.Trigger>
						<Tooltip.Portal>
							<Tooltip.Content side="right">
								{item.label}
							</Tooltip.Content>
						</Tooltip.Portal>
					</Tooltip.Root>
				{:else}
					<a
						href={item.href}
						class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground {isActive(item.href) ? 'bg-accent text-accent-foreground' : ''}"
					>
						<Icon class="h-4 w-4" />
						{item.label}
					</a>
				{/if}
			{/each}
		</nav>
	</ScrollArea>

	<!-- User Avatar & Toggle button -->
	<div class="border-t p-2">
		{#if collapsed}
			<!-- Collapsed: User avatar icon -->
			{#if user}
				<Tooltip.Root>
					<Tooltip.Trigger>
						{#snippet child({ props })}
							<DropdownMenu.Root>
								<DropdownMenu.Trigger>
									{#snippet child({ props: triggerProps })}
										<button {...props} {...triggerProps} class="flex w-full items-center justify-center rounded-lg p-2 hover:bg-accent">
											<Avatar.Root class="h-8 w-8">
												{#if user.avatar}
													<Avatar.Image src={user.avatar} alt={user.name} />
												{/if}
												<Avatar.Fallback>{user.name.slice(0, 2).toUpperCase()}</Avatar.Fallback>
											</Avatar.Root>
										</button>
									{/snippet}
								</DropdownMenu.Trigger>
								<DropdownMenu.Content class="w-56" side="right" align="end">
									<DropdownMenu.Label class="font-normal">
										<div class="flex flex-col space-y-1">
											<p class="text-sm font-medium leading-none">{user.name}</p>
											<p class="text-xs leading-none text-muted-foreground">{user.email}</p>
										</div>
									</DropdownMenu.Label>
									<DropdownMenu.Separator />
									<DropdownMenu.Item>
										<a href="/settings" class="flex items-center">
											<User class="mr-2 h-4 w-4" />
											Profile
										</a>
									</DropdownMenu.Item>
									<DropdownMenu.Item>
										<a href="/settings" class="flex items-center">
											<Settings class="mr-2 h-4 w-4" />
											Settings
										</a>
									</DropdownMenu.Item>
									<DropdownMenu.Separator />
									<DropdownMenu.Item onclick={onLogout}>
										<LogOut class="mr-2 h-4 w-4" />
										Log out
									</DropdownMenu.Item>
								</DropdownMenu.Content>
							</DropdownMenu.Root>
						{/snippet}
					</Tooltip.Trigger>
					<Tooltip.Portal>
						<Tooltip.Content side="right">
							{user.name}
						</Tooltip.Content>
					</Tooltip.Portal>
				</Tooltip.Root>
			{/if}
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<Button {...props} variant="ghost" size="icon" class="w-full" onclick={onToggle}>
							<ChevronRight class="h-4 w-4" />
						</Button>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Portal>
					<Tooltip.Content side="right">
						Expand sidebar
					</Tooltip.Content>
				</Tooltip.Portal>
			</Tooltip.Root>
		{:else}
			<!-- Expanded: User info + logout -->
			{#if user}
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<button {...props} class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-accent">
								<Avatar.Root class="h-8 w-8">
									{#if user.avatar}
										<Avatar.Image src={user.avatar} alt={user.name} />
									{/if}
									<Avatar.Fallback>{user.name.slice(0, 2).toUpperCase()}</Avatar.Fallback>
								</Avatar.Root>
								<div class="flex-1 text-left">
									<p class="text-sm font-medium leading-none">{user.name}</p>
									<p class="text-xs text-muted-foreground truncate">{user.email}</p>
								</div>
							</button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content class="w-56" side="right" align="end">
						<DropdownMenu.Item>
							<a href="/settings" class="flex items-center">
								<User class="mr-2 h-4 w-4" />
								Profile
							</a>
						</DropdownMenu.Item>
						<DropdownMenu.Item>
							<a href="/settings" class="flex items-center">
								<Settings class="mr-2 h-4 w-4" />
								Settings
							</a>
						</DropdownMenu.Item>
						<DropdownMenu.Separator />
						<DropdownMenu.Item onclick={onLogout}>
							<LogOut class="mr-2 h-4 w-4" />
							Log out
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			{/if}
			<Button variant="ghost" class="w-full justify-start mt-2" onclick={onToggle}>
				<ChevronLeft class="mr-2 h-4 w-4" />
				Collapse
			</Button>
		{/if}
	</div>
</aside>
