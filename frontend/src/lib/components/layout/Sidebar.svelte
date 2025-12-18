<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import * as Tooltip from '$lib/components/ui/tooltip';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Avatar from '$lib/components/ui/avatar';
	import { MessageSquare, MessageSquarePlus, FileText, Bot, ChevronLeft, ChevronRight, LogOut, User, Settings, Image, Folder, Trash2, Loader2, Bell, Sparkles, Workflow } from 'lucide-svelte';
	import { chatStore, type Conversation, notificationStore } from '$lib/stores';
	import * as m from '$lib/paraglide/messages';

	let {
		collapsed = false,
		onToggle,
		user,
		onLogout
	} = $props<{
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

	// navItems needs to be derived to react to locale changes
	let navItems = $derived<NavItem[]>([
		{ label: m.nav_new_chat(), href: '/chat', icon: MessageSquarePlus },
		{ label: m.nav_chats(), href: '/chats', icon: MessageSquare },
		{ label: m.nav_images(), href: '/images', icon: Image },
		{ label: m.nav_documents(), href: '/documents', icon: FileText },
		{ label: m.nav_projects(), href: '/projects', icon: Folder },
		{ label: m.nav_agents(), href: '/agents', icon: Bot },
		{ label: 'Workflows', href: '/workflows', icon: Workflow },
		{ label: m.nav_notifications(), href: '/notifications', icon: Bell },
	]);

	let chatHistoryContainer = $state<HTMLDivElement | null>(null);
	let hoveredChatId = $state<string | null>(null);

	// Load initial chats
	onMount(() => {
		if (!chatStore.initialized) {
			chatStore.loadInitial();
		}
	});

	// Track current chat ID from URL
	$effect(() => {
		const match = $page.url.pathname.match(/^\/chat\/([^/]+)/);
		chatStore.setCurrentId(match ? match[1] : null);
	});

	function isActive(href: string): boolean {
		const pathname = $page.url.pathname;
		if (href === '/chat') {
			return pathname === '/chat';
		}
		return pathname.startsWith(href);
	}

	function isChatActive(id: string): boolean {
		return $page.url.pathname === `/chat/${id}`;
	}

	function getDisplayTitle(conv: Conversation): string {
		if (conv.title) return conv.title;
		if (conv.last_message_preview) {
			return conv.last_message_preview.length > 25
				? conv.last_message_preview.substring(0, 25) + '...'
				: conv.last_message_preview;
		}
		return m.sidebar_new_conversation();
	}

	async function handleDeleteChat(e: MouseEvent, id: string) {
		e.preventDefault();
		e.stopPropagation();
		try {
			await chatStore.delete(id);
			if (chatStore.currentId === id) {
				goto('/chat');
			}
		} catch (e) {
			console.error('Failed to delete:', e);
		}
	}

	function handleScroll(e: Event) {
		const target = e.target as HTMLDivElement;
		const { scrollTop, scrollHeight, clientHeight } = target;

		// Load more when scrolled near bottom (within 50px)
		if (scrollHeight - scrollTop - clientHeight < 50) {
			chatStore.loadMore();
		}
	}
</script>

<aside
	class="flex h-full flex-col border-r bg-background transition-all duration-300 {collapsed
		? 'w-16'
		: 'w-64'}"
>
	<!-- Logo & Platform Name -->
	{#if !collapsed}
		<div class="flex items-center gap-2 p-4">
			<div class="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center">
				<svg class="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
				</svg>
			</div>
			<span class="font-semibold">RAG Agent</span>
		</div>
	{:else}
		<div class="flex justify-center p-4">
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<div {...props} class="h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center">
							<svg class="h-5 w-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
							</svg>
						</div>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Portal>
					<Tooltip.Content side="right">RAG Agent</Tooltip.Content>
				</Tooltip.Portal>
			</Tooltip.Root>
		</div>
	{/if}
	<Separator />

	<!-- Navigation -->
	<div class="px-2 py-4">
		<nav class="flex flex-col gap-1">
			{#each navItems as item}
				{@const Icon = item.icon}
				{@const isNotification = item.href === '/notifications'}
				{@const unreadCount = isNotification ? notificationStore.unreadCount : 0}
				{#if collapsed}
					<Tooltip.Root>
						<Tooltip.Trigger>
							{#snippet child({ props })}
								<a
									{...props}
									href={item.href}
									class="relative flex items-center justify-center rounded-lg p-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground {isActive(
										item.href
									)
										? 'bg-accent text-accent-foreground'
										: ''}"
								>
									<Icon class="h-5 w-5" />
									{#if isNotification && unreadCount > 0}
										<span class="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground">
											{unreadCount > 9 ? '9+' : unreadCount}
										</span>
									{/if}
								</a>
							{/snippet}
						</Tooltip.Trigger>
						<Tooltip.Portal>
							<Tooltip.Content side="right">
								{item.label}
								{#if isNotification && unreadCount > 0}
									<span class="ml-1 text-muted-foreground">({unreadCount})</span>
								{/if}
							</Tooltip.Content>
						</Tooltip.Portal>
					</Tooltip.Root>
				{:else}
					<a
						href={item.href}
						class="flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground {isActive(
							item.href
						)
							? 'bg-accent text-accent-foreground'
							: ''}"
					>
						<div class="relative">
							<Icon class="h-4 w-4" />
							{#if isNotification && unreadCount > 0}
								<span class="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-destructive text-[8px] font-medium text-destructive-foreground">
									{unreadCount > 9 ? '!' : unreadCount}
								</span>
							{/if}
						</div>
						{item.label}
						{#if isNotification && unreadCount > 0}
							<span class="ml-auto rounded-full bg-destructive px-1.5 py-0.5 text-[10px] font-medium text-destructive-foreground">
								{unreadCount > 99 ? '99+' : unreadCount}
							</span>
						{/if}
					</a>
				{/if}
			{/each}
		</nav>
	</div>

	<!-- Chat History (only when expanded) -->
	{#if !collapsed}
		<div class="flex items-center justify-between px-4 py-2">
			<span class="text-xs font-medium text-muted-foreground">{m.sidebar_recent_chats()}</span>
			{#if chatStore.loading}
				<Loader2 class="h-3 w-3 animate-spin text-muted-foreground" />
			{/if}
		</div>
		<div
			bind:this={chatHistoryContainer}
			class="flex-1 overflow-y-auto px-2"
			onscroll={handleScroll}
		>
			{#if chatStore.loading && chatStore.conversations.length === 0}
				<!-- Loading skeleton -->
				<div class="space-y-1">
					{#each Array(5) as _}
						<div class="h-8 animate-pulse rounded-lg bg-muted"></div>
					{/each}
				</div>
			{:else if chatStore.conversations.length === 0}
				<div
					class="flex flex-col items-center justify-center py-4 text-center text-muted-foreground"
				>
					<MessageSquare class="mb-2 h-6 w-6 opacity-50" />
					<p class="text-xs">{m.sidebar_no_chats()}</p>
				</div>
			{:else}
				<div class="space-y-0.5">
					{#each chatStore.conversations as conv (conv.id)}
						<a
							href="/chat/{conv.id}"
							class="group flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors hover:bg-accent {isChatActive(
								conv.id
							)
								? 'bg-accent'
								: ''}"
							onmouseenter={() => (hoveredChatId = conv.id)}
							onmouseleave={() => (hoveredChatId = null)}
						>
							<MessageSquare class="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
							<span class="flex-1 truncate text-xs">{getDisplayTitle(conv)}</span>
							{#if hoveredChatId === conv.id}
								<button
									class="shrink-0 rounded p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
									onclick={(e) => handleDeleteChat(e, conv.id)}
								>
									<Trash2 class="h-3.5 w-3.5" />
								</button>
							{/if}
						</a>
					{/each}
				</div>

				<!-- Load more indicator -->
				{#if chatStore.loadingMore}
					<div class="flex justify-center py-2">
						<Loader2 class="h-4 w-4 animate-spin text-muted-foreground" />
					</div>
				{/if}
			{/if}
		</div>
	{/if}

	<!-- User Avatar & Toggle button -->
	<div class="mt-auto p-2">
		{#if collapsed}
			<!-- Collapsed: User avatar icon -->
			{#if user}
				<Tooltip.Root>
					<Tooltip.Trigger>
						{#snippet child({ props })}
							<DropdownMenu.Root>
								<DropdownMenu.Trigger>
									{#snippet child({ props: triggerProps })}
										<button
											{...props}
											{...triggerProps}
											class="flex w-full items-center justify-center rounded-lg p-2 hover:bg-accent"
										>
											<Avatar.Root class="h-8 w-8 cursor-pointer">
												{#if user.avatar}
													<Avatar.Image
														src={user.avatar}
														alt={user.name}
													/>
												{/if}
												<Avatar.Fallback
													>{user.name
														.slice(0, 2)
														.toUpperCase()}</Avatar.Fallback
												>
											</Avatar.Root>
										</button>
									{/snippet}
								</DropdownMenu.Trigger>
								<DropdownMenu.Content class="w-56" side="right" align="end">
									<DropdownMenu.Label class="font-normal">
										<div class="flex flex-col space-y-1">
											<p class="text-sm font-medium leading-none">
												{user.name}
											</p>
											<p class="text-xs leading-none text-muted-foreground">
												{user.email}
											</p>
										</div>
									</DropdownMenu.Label>
									<DropdownMenu.Separator />
									<DropdownMenu.Item>
										<a href="/settings" class="flex items-center">
											<Settings class="mr-2 h-4 w-4" />
											{m.nav_settings()}
										</a>
									</DropdownMenu.Item>
									<DropdownMenu.Item>
										<a href="/settings?tab=billing" class="flex items-center text-primary">
											<Sparkles class="mr-2 h-4 w-4" />
											{m.nav_upgrade_plan()}
										</a>
									</DropdownMenu.Item>
									<DropdownMenu.Separator />
									<DropdownMenu.Item onclick={onLogout}>
										<LogOut class="mr-2 h-4 w-4" />
										{m.nav_logout()}
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
						<Button
							{...props}
							variant="ghost"
							size="icon"
							class="w-full"
							onclick={onToggle}
						>
							<ChevronRight class="h-4 w-4" />
						</Button>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Portal>
					<Tooltip.Content side="right">{m.nav_expand_sidebar()}</Tooltip.Content>
				</Tooltip.Portal>
			</Tooltip.Root>
		{:else}
			<!-- Expanded: User info + logout -->
			{#if user}
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<button
								{...props}
								class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-accent cursor-pointer"
							>
								<Avatar.Root class="h-8 w-8 cursor-pointer">
									{#if user.avatar}
										<Avatar.Image src={user.avatar} alt={user.name} />
									{/if}
									<Avatar.Fallback
										>{user.name.slice(0, 2).toUpperCase()}</Avatar.Fallback
									>
								</Avatar.Root>
								<div class="flex-1 text-left">
									<p class="text-sm font-medium leading-none">{user.name}</p>
									<p class="text-xs text-muted-foreground truncate">
										{user.email}
									</p>
								</div>
							</button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content class="w-56" side="right" align="end">
						<DropdownMenu.Item class="cursor-pointer">
							<a href="/settings" class="flex items-center">
								<Settings class="mr-2 h-4 w-4" />
								{m.nav_settings()}
							</a>
						</DropdownMenu.Item>
						<DropdownMenu.Item class="cursor-pointer">
							<a href="/settings?tab=billing" class="flex items-center text-primary">
								<Sparkles class="mr-2 h-4 w-4" />
								{m.nav_upgrade_plan()}
							</a>
						</DropdownMenu.Item>
						<DropdownMenu.Separator />
						<DropdownMenu.Item onclick={onLogout}>
							<LogOut class="mr-2 h-4 w-4" />
							{m.nav_logout()}
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			{/if}
			<Button variant="ghost" class="w-full justify-start mt-2" onclick={onToggle}>
				<ChevronLeft class="mr-2 h-4 w-4" />
				{m.nav_collapse()}
			</Button>
		{/if}
	</div>
</aside>
