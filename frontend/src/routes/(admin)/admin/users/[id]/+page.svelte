<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Card } from '$lib/components/ui/card';
	import { Separator } from '$lib/components/ui/separator';
	import { Progress } from '$lib/components/ui/progress';
	import * as Avatar from '$lib/components/ui/avatar';
	import * as Tabs from '$lib/components/ui/tabs';
	import * as Table from '$lib/components/ui/table';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import {
		ArrowLeft,
		Mail,
		User,
		Calendar,
		Shield,
		CreditCard,
		MessageSquare,
		FileText,
		FolderOpen,
		DollarSign,
		Activity,
		MoreHorizontal,
		Ban,
		UserCheck,
		UserX,
		Trash2,
		Edit
	} from 'lucide-svelte';
	import {
		getUserDetail,
		getPlans,
		suspendUser,
		activateUser,
		banUser,
		deleteUser,
		changeUserPlan,
		type UserDetail,
		type Plan
	} from '$lib/api/admin';

	let user = $state<UserDetail | null>(null);
	let plans = $state<Plan[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Confirmation dialog state
	let confirmDialog = $state<{
		open: boolean;
		title: string;
		description: string;
		variant: 'default' | 'destructive';
		action: () => Promise<void>;
	}>({
		open: false,
		title: '',
		description: '',
		variant: 'default',
		action: async () => {}
	});

	const userId = $derived($page.params.id);

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		if (!userId) {
			error = 'User ID is required';
			loading = false;
			return;
		}
		try {
			loading = true;
			const [userData, plansData] = await Promise.all([getUserDetail(userId), getPlans()]);
			user = userData;
			plans = plansData.items;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load user';
		} finally {
			loading = false;
		}
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function formatDateTime(dateStr: string | null): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function formatCurrency(amount: number, currency: string = 'USD'): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency
		}).format(amount);
	}

	function formatFileSize(bytes: number): string {
		if (bytes === 0) return '0 Bytes';
		const k = 1024;
		const sizes = ['Bytes', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}

	function formatNumber(num: number): string {
		return new Intl.NumberFormat('en-US').format(num);
	}

	function getStatusVariant(
		status: string
	): 'default' | 'secondary' | 'destructive' | 'outline' {
		switch (status.toLowerCase()) {
			case 'active':
			case 'paid':
			case 'ready':
				return 'default';
			case 'trialing':
			case 'processing':
			case 'pending':
				return 'secondary';
			case 'canceled':
			case 'past_due':
			case 'error':
			case 'void':
				return 'destructive';
			default:
				return 'outline';
		}
	}

	function openConfirmDialog(
		title: string,
		description: string,
		variant: 'default' | 'destructive',
		action: () => Promise<void>
	) {
		confirmDialog = { open: true, title, description, variant, action };
	}

	async function executeConfirmAction() {
		try {
			await confirmDialog.action();
		} finally {
			confirmDialog.open = false;
		}
	}

	function handleSuspend() {
		if (!user) return;
		openConfirmDialog(
			'Suspend User',
			'Are you sure you want to suspend this user?',
			'default',
			async () => {
				try {
					await suspendUser(user!.id);
					await loadData();
					toast.success('User suspended successfully');
				} catch (e) {
					toast.error('Failed to suspend user');
				}
			}
		);
	}

	async function handleActivate() {
		if (!user) return;
		try {
			await activateUser(user.id);
			await loadData();
			toast.success('User activated successfully');
		} catch (e) {
			toast.error('Failed to activate user');
		}
	}

	function handleBan() {
		if (!user) return;
		openConfirmDialog(
			'Ban User',
			'Are you sure you want to ban this user? This action is severe.',
			'destructive',
			async () => {
				try {
					await banUser(user!.id);
					await loadData();
					toast.success('User banned successfully');
				} catch (e) {
					toast.error('Failed to ban user');
				}
			}
		);
	}

	function handleDelete() {
		if (!user) return;
		openConfirmDialog(
			'Delete User',
			'Are you sure you want to DELETE this user? This action cannot be undone.',
			'destructive',
			async () => {
				try {
					await deleteUser(user!.id);
					toast.success('User deleted successfully');
					goto('/admin/users');
				} catch (e) {
					toast.error('Failed to delete user');
				}
			}
		);
	}

	async function handleChangePlan(planId: string) {
		if (!user) return;
		try {
			await changeUserPlan(user.id, planId);
			await loadData();
			toast.success('Plan changed successfully');
		} catch (e) {
			toast.error('Failed to change plan');
		}
	}

	// Calculate usage percentage
	let usagePercentage = $derived(
		user?.usage.tokens_limit
			? Math.min(100, (user.usage.tokens_used_this_month / user.usage.tokens_limit) * 100)
			: 0
	);
</script>

<svelte:head>
	<title>{user ? `${user.email} - User Details` : 'User Details'} | Admin</title>
</svelte:head>

<div class="flex-1 space-y-6 p-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<Button variant="ghost" size="icon" href="/admin/users">
				<ArrowLeft class="h-4 w-4" />
			</Button>
			<div>
				<h1 class="text-2xl font-bold">User Details</h1>
				{#if user}
					<p class="text-muted-foreground">{user.email}</p>
				{/if}
			</div>
		</div>

		{#if user}
			<div class="flex items-center gap-2">
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Button {...props} variant="outline">
								<MoreHorizontal class="mr-2 h-4 w-4" />
								Actions
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end">
						<DropdownMenu.Label>User Actions</DropdownMenu.Label>
						<DropdownMenu.Separator />
						{#if user.is_active}
							<DropdownMenu.Item onclick={handleSuspend}>
								<UserX class="mr-2 h-4 w-4" />
								Suspend User
							</DropdownMenu.Item>
						{:else}
							<DropdownMenu.Item onclick={handleActivate}>
								<UserCheck class="mr-2 h-4 w-4" />
								Activate User
							</DropdownMenu.Item>
						{/if}
						<DropdownMenu.Item onclick={handleBan} class="text-orange-600">
							<Ban class="mr-2 h-4 w-4" />
							Ban User
						</DropdownMenu.Item>
						<DropdownMenu.Separator />
						<DropdownMenu.Item onclick={handleDelete} class="text-destructive">
							<Trash2 class="mr-2 h-4 w-4" />
							Delete User
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			</div>
		{/if}
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent">
			</div>
		</div>
	{:else if error}
		<Card class="p-6">
			<p class="text-destructive">{error}</p>
			<Button onclick={loadData} class="mt-4">Retry</Button>
		</Card>
	{:else if user}
		<div class="grid gap-6 lg:grid-cols-3">
			<!-- Left Column: Profile & Quick Stats -->
			<div class="space-y-6">
				<!-- Profile Card -->
				<Card class="p-6">
					<div class="flex items-start gap-4">
						<Avatar.Root class="h-16 w-16">
							<Avatar.Fallback class="text-lg">
								{user.email.slice(0, 2).toUpperCase()}
							</Avatar.Fallback>
						</Avatar.Root>
						<div class="flex-1">
							<div class="flex items-center gap-2">
								<h2 class="text-lg font-semibold">
									{user.first_name || user.last_name
										? `${user.first_name || ''} ${user.last_name || ''}`.trim()
										: user.username}
								</h2>
								{#if user.is_superuser}
									<Badge variant="default">Admin</Badge>
								{/if}
							</div>
							<p class="text-sm text-muted-foreground">@{user.username}</p>
							<Badge variant={user.is_active ? 'default' : 'destructive'} class="mt-2">
								{user.is_active ? 'Active' : 'Inactive'}
							</Badge>
						</div>
					</div>

					<Separator class="my-4" />

					<div class="space-y-3 text-sm">
						<div class="flex items-center gap-2 text-muted-foreground">
							<Mail class="h-4 w-4" />
							<span>{user.email}</span>
						</div>
						<div class="flex items-center gap-2 text-muted-foreground">
							<Shield class="h-4 w-4" />
							<span>Tier: {user.tier}</span>
						</div>
						<div class="flex items-center gap-2 text-muted-foreground">
							<Calendar class="h-4 w-4" />
							<span>Joined {formatDate(user.created_at)}</span>
						</div>
					</div>
				</Card>

				<!-- Quick Stats -->
				<Card class="p-6">
					<h3 class="mb-4 font-semibold">Quick Stats</h3>
					<div class="grid grid-cols-2 gap-4">
						<div class="rounded-lg bg-muted/50 p-3 text-center">
							<MessageSquare class="mx-auto h-5 w-5 text-muted-foreground" />
							<p class="mt-1 text-2xl font-bold">{user.total_conversations}</p>
							<p class="text-xs text-muted-foreground">Conversations</p>
						</div>
						<div class="rounded-lg bg-muted/50 p-3 text-center">
							<FileText class="mx-auto h-5 w-5 text-muted-foreground" />
							<p class="mt-1 text-2xl font-bold">{user.total_documents}</p>
							<p class="text-xs text-muted-foreground">Documents</p>
						</div>
						<div class="rounded-lg bg-muted/50 p-3 text-center">
							<FolderOpen class="mx-auto h-5 w-5 text-muted-foreground" />
							<p class="mt-1 text-2xl font-bold">{user.total_projects}</p>
							<p class="text-xs text-muted-foreground">Projects</p>
						</div>
						<div class="rounded-lg bg-muted/50 p-3 text-center">
							<DollarSign class="mx-auto h-5 w-5 text-muted-foreground" />
							<p class="mt-1 text-2xl font-bold">{formatCurrency(user.total_revenue)}</p>
							<p class="text-xs text-muted-foreground">Revenue</p>
						</div>
					</div>
				</Card>

				<!-- Current Plan -->
				<Card class="p-6">
					<div class="mb-4 flex items-center justify-between">
						<h3 class="font-semibold">Current Plan</h3>
						<DropdownMenu.Root>
							<DropdownMenu.Trigger>
								{#snippet child({ props })}
									<Button {...props} variant="outline" size="sm">
										<Edit class="mr-2 h-3 w-3" />
										Change
									</Button>
								{/snippet}
							</DropdownMenu.Trigger>
							<DropdownMenu.Content>
								<DropdownMenu.Label>Select Plan</DropdownMenu.Label>
								<DropdownMenu.Separator />
								{#each plans as plan}
									<DropdownMenu.Item onclick={() => handleChangePlan(plan.id)}>
										{plan.display_name} - {formatCurrency(plan.price_monthly)}/mo
									</DropdownMenu.Item>
								{/each}
							</DropdownMenu.Content>
						</DropdownMenu.Root>
					</div>

					{#if user.active_subscription}
						<div class="rounded-lg border p-4">
							<div class="flex items-center justify-between">
								<div>
									<p class="font-medium">{user.active_subscription.plan_display_name}</p>
									<p class="text-sm text-muted-foreground">
										{formatCurrency(user.active_subscription.price)}/{user.active_subscription
											.billing_interval}
									</p>
								</div>
								<Badge variant={getStatusVariant(user.active_subscription.status)}>
									{user.active_subscription.status}
								</Badge>
							</div>
							{#if user.active_subscription.current_period_end}
								<p class="mt-2 text-xs text-muted-foreground">
									Renews {formatDate(user.active_subscription.current_period_end)}
								</p>
							{/if}
						</div>
					{:else}
						<p class="text-sm text-muted-foreground">No active subscription</p>
					{/if}
				</Card>
			</div>

			<!-- Right Column: Detailed Info -->
			<div class="space-y-6 lg:col-span-2">
				<!-- Usage Stats -->
				<Card class="p-6">
					<h3 class="mb-4 font-semibold">Usage Statistics</h3>
					<div class="grid gap-4 md:grid-cols-3">
						<div>
							<p class="text-sm text-muted-foreground">Tokens Used (This Month)</p>
							<p class="text-2xl font-bold">{formatNumber(user.usage.tokens_used_this_month)}</p>
							<div class="mt-2">
								<Progress value={usagePercentage} class="h-2" />
								<p class="mt-1 text-xs text-muted-foreground">
									{formatNumber(user.usage.tokens_limit)} limit
								</p>
							</div>
						</div>
						<div>
							<p class="text-sm text-muted-foreground">Requests (This Month)</p>
							<p class="text-2xl font-bold">{formatNumber(user.usage.requests_this_month)}</p>
							<p class="text-xs text-muted-foreground">
								{formatNumber(user.usage.requests_today)} today
							</p>
						</div>
						<div>
							<p class="text-sm text-muted-foreground">Cost (This Month)</p>
							<p class="text-2xl font-bold">{formatCurrency(user.usage.cost_this_month)}</p>
							<p class="text-xs text-muted-foreground">
								{formatCurrency(user.usage.cost_today)} today
							</p>
						</div>
					</div>

					<!-- Usage Chart Placeholder -->
					<div class="mt-6 h-48 rounded-lg border bg-muted/20 p-4">
						<p class="text-center text-sm text-muted-foreground">
							Usage chart will be displayed here
						</p>
					</div>
				</Card>

				<!-- Tabs for Details -->
				<Tabs.Root value="conversations">
					<Tabs.List class="grid w-full grid-cols-4">
						<Tabs.Trigger value="conversations">Conversations</Tabs.Trigger>
						<Tabs.Trigger value="documents">Documents</Tabs.Trigger>
						<Tabs.Trigger value="subscriptions">Subscriptions</Tabs.Trigger>
						<Tabs.Trigger value="invoices">Invoices</Tabs.Trigger>
					</Tabs.List>

					<!-- Recent Conversations -->
					<Tabs.Content value="conversations" class="mt-4">
						<Card>
							<Table.Root>
								<Table.Header>
									<Table.Row>
										<Table.Head>Title</Table.Head>
										<Table.Head>Messages</Table.Head>
										<Table.Head>Last Message</Table.Head>
										<Table.Head>Created</Table.Head>
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{#if user.recent_conversations.length === 0}
										<Table.Row>
											<Table.Cell colspan={4} class="text-center text-muted-foreground">
												No conversations found
											</Table.Cell>
										</Table.Row>
									{:else}
										{#each user.recent_conversations as conv}
											<Table.Row>
												<Table.Cell class="font-medium">
													{conv.title || 'Untitled'}
												</Table.Cell>
												<Table.Cell>{conv.message_count}</Table.Cell>
												<Table.Cell>{formatDateTime(conv.last_message_at)}</Table.Cell>
												<Table.Cell>{formatDate(conv.created_at)}</Table.Cell>
											</Table.Row>
										{/each}
									{/if}
								</Table.Body>
							</Table.Root>
						</Card>
					</Tabs.Content>

					<!-- Recent Documents -->
					<Tabs.Content value="documents" class="mt-4">
						<Card>
							<Table.Root>
								<Table.Header>
									<Table.Row>
										<Table.Head>Filename</Table.Head>
										<Table.Head>Type</Table.Head>
										<Table.Head>Size</Table.Head>
										<Table.Head>Status</Table.Head>
										<Table.Head>Chunks</Table.Head>
										<Table.Head>Created</Table.Head>
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{#if user.recent_documents.length === 0}
										<Table.Row>
											<Table.Cell colspan={6} class="text-center text-muted-foreground">
												No documents found
											</Table.Cell>
										</Table.Row>
									{:else}
										{#each user.recent_documents as doc}
											<Table.Row>
												<Table.Cell class="max-w-[200px] truncate font-medium">
													{doc.filename}
												</Table.Cell>
												<Table.Cell>
													<Badge variant="outline">{doc.file_type}</Badge>
												</Table.Cell>
												<Table.Cell>{formatFileSize(doc.file_size)}</Table.Cell>
												<Table.Cell>
													<Badge variant={getStatusVariant(doc.status)}>{doc.status}</Badge>
												</Table.Cell>
												<Table.Cell>{doc.chunk_count}</Table.Cell>
												<Table.Cell>{formatDate(doc.created_at)}</Table.Cell>
											</Table.Row>
										{/each}
									{/if}
								</Table.Body>
							</Table.Root>
						</Card>
					</Tabs.Content>

					<!-- Subscription History -->
					<Tabs.Content value="subscriptions" class="mt-4">
						<Card>
							<Table.Root>
								<Table.Header>
									<Table.Row>
										<Table.Head>Plan</Table.Head>
										<Table.Head>Status</Table.Head>
										<Table.Head>Billing</Table.Head>
										<Table.Head>Price</Table.Head>
										<Table.Head>Start Date</Table.Head>
										<Table.Head>End Date</Table.Head>
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{#if user.subscription_history.length === 0}
										<Table.Row>
											<Table.Cell colspan={6} class="text-center text-muted-foreground">
												No subscription history
											</Table.Cell>
										</Table.Row>
									{:else}
										{#each user.subscription_history as sub}
											<Table.Row>
												<Table.Cell class="font-medium">{sub.plan_display_name}</Table.Cell>
												<Table.Cell>
													<Badge variant={getStatusVariant(sub.status)}>{sub.status}</Badge>
												</Table.Cell>
												<Table.Cell>{sub.billing_interval}</Table.Cell>
												<Table.Cell>{formatCurrency(sub.price)}</Table.Cell>
												<Table.Cell>{formatDate(sub.start_date)}</Table.Cell>
												<Table.Cell>
													{sub.canceled_at ? formatDate(sub.canceled_at) : '-'}
												</Table.Cell>
											</Table.Row>
										{/each}
									{/if}
								</Table.Body>
							</Table.Root>
						</Card>
					</Tabs.Content>

					<!-- Invoices -->
					<Tabs.Content value="invoices" class="mt-4">
						<Card>
							<Table.Root>
								<Table.Header>
									<Table.Row>
										<Table.Head>Invoice #</Table.Head>
										<Table.Head>Status</Table.Head>
										<Table.Head>Total</Table.Head>
										<Table.Head>Paid</Table.Head>
										<Table.Head>Date</Table.Head>
										<Table.Head>Paid At</Table.Head>
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{#if user.invoices.length === 0}
										<Table.Row>
											<Table.Cell colspan={6} class="text-center text-muted-foreground">
												No invoices found
											</Table.Cell>
										</Table.Row>
									{:else}
										{#each user.invoices as inv}
											<Table.Row>
												<Table.Cell class="font-medium">{inv.invoice_number}</Table.Cell>
												<Table.Cell>
													<Badge variant={getStatusVariant(inv.status)}>{inv.status}</Badge>
												</Table.Cell>
												<Table.Cell>{formatCurrency(inv.total, inv.currency)}</Table.Cell>
												<Table.Cell>{formatCurrency(inv.amount_paid, inv.currency)}</Table.Cell>
												<Table.Cell>{formatDate(inv.invoice_date)}</Table.Cell>
												<Table.Cell>{formatDate(inv.paid_at)}</Table.Cell>
											</Table.Row>
										{/each}
									{/if}
								</Table.Body>
							</Table.Root>
						</Card>
					</Tabs.Content>
				</Tabs.Root>
			</div>
		</div>
	{/if}
</div>

<!-- Confirmation Dialog -->
<AlertDialog.Root bind:open={confirmDialog.open}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>{confirmDialog.title}</AlertDialog.Title>
			<AlertDialog.Description>{confirmDialog.description}</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
			<AlertDialog.Action
				onclick={executeConfirmAction}
				class={confirmDialog.variant === 'destructive' ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90' : ''}
			>
				Confirm
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
