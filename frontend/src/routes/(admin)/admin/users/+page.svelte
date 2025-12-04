<script lang="ts">
	import { onMount } from 'svelte';
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Progress } from '$lib/components/ui/progress';
	import * as Select from '$lib/components/ui/select';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Table from '$lib/components/ui/table';
	import {
		getUsers,
		getPlans,
		suspendUser,
		activateUser,
		banUser,
		deleteUser,
		changeUserPlan,
		bulkUserAction,
		type AdminUser,
		type Plan
	} from '$lib/api/admin';
	import {
		Search,
		MoreHorizontal,
		Pencil,
		UserX,
		UserCheck,
		Ban,
		Trash2,
		CreditCard,
		ChevronLeft,
		ChevronRight,
		Users
	} from 'lucide-svelte';
	import { toast } from 'svelte-sonner';

	let users = $state<AdminUser[]>([]);
	let plans = $state<Plan[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Pagination
	let page = $state(1);
	let perPage = $state(20);
	let totalUsers = $state(0);
	let totalPages = $state(0);

	// Filters
	let searchQuery = $state('');
	let planFilter = $state('all');
	let statusFilter = $state('all');
	let searchTimeout: ReturnType<typeof setTimeout>;

	// Selection for bulk actions
	let selectedUsers = $state<Set<string>>(new Set());
	let selectAll = $state(false);

	// Action dialogs
	let actionUser = $state<AdminUser | null>(null);
	let actionType = $state<'suspend' | 'ban' | 'delete' | 'changePlan' | null>(null);
	let actionReason = $state('');
	let selectedPlanId = $state('');
	let actionLoading = $state(false);

	// Bulk action dialog
	let showBulkDialog = $state(false);
	let bulkAction = $state<'suspend' | 'activate' | 'change_plan' | null>(null);
	let bulkPlanId = $state('');

	onMount(async () => {
		await Promise.all([loadUsers(), loadPlans()]);
	});

	async function loadUsers() {
		loading = true;
		error = null;
		try {
			const filters: { search?: string; plan?: string; status?: string } = {};
			if (searchQuery) filters.search = searchQuery;
			if (planFilter !== 'all') filters.plan = planFilter;
			if (statusFilter !== 'all') filters.status = statusFilter;

			const response = await getUsers(page, perPage, filters);
			users = response.items;
			totalUsers = response.total;
			totalPages = response.pages;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load users';
		} finally {
			loading = false;
		}
	}

	async function loadPlans() {
		try {
			const response = await getPlans(1, 100, true);
			plans = response.items;
		} catch (e) {
			console.error('Failed to load plans:', e);
		}
	}

	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			searchQuery = target.value;
			page = 1;
			loadUsers();
		}, 300);
	}

	function handlePlanFilterChange(value: string | undefined) {
		if (value) {
			planFilter = value;
			page = 1;
			loadUsers();
		}
	}

	function handleStatusFilterChange(value: string | undefined) {
		if (value) {
			statusFilter = value;
			page = 1;
			loadUsers();
		}
	}

	function toggleSelectAll() {
		if (selectAll) {
			selectedUsers = new Set();
		} else {
			selectedUsers = new Set(users.map((u) => u.id));
		}
		selectAll = !selectAll;
	}

	function toggleUserSelection(userId: string) {
		const newSet = new Set(selectedUsers);
		if (newSet.has(userId)) {
			newSet.delete(userId);
		} else {
			newSet.add(userId);
		}
		selectedUsers = newSet;
		selectAll = selectedUsers.size === users.length;
	}

	function openActionDialog(user: AdminUser, type: 'suspend' | 'ban' | 'delete' | 'changePlan') {
		actionUser = user;
		actionType = type;
		actionReason = '';
		selectedPlanId = '';
	}

	function closeActionDialog() {
		actionUser = null;
		actionType = null;
		actionReason = '';
		selectedPlanId = '';
	}

	async function executeAction() {
		if (!actionUser || !actionType) return;

		actionLoading = true;
		try {
			switch (actionType) {
				case 'suspend':
					await suspendUser(actionUser.id, actionReason || undefined);
					toast.success('User suspended successfully');
					break;
				case 'ban':
					await banUser(actionUser.id, actionReason || undefined);
					toast.success('User banned successfully');
					break;
				case 'delete':
					await deleteUser(actionUser.id);
					toast.success('User deleted successfully');
					break;
				case 'changePlan':
					if (!selectedPlanId) {
						toast.error('Please select a plan');
						return;
					}
					await changeUserPlan(actionUser.id, selectedPlanId);
					toast.success('User plan changed successfully');
					break;
			}
			closeActionDialog();
			await loadUsers();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : 'Action failed');
		} finally {
			actionLoading = false;
		}
	}

	async function handleActivateUser(user: AdminUser) {
		try {
			await activateUser(user.id);
			toast.success('User activated successfully');
			await loadUsers();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : 'Failed to activate user');
		}
	}

	function openBulkDialog(action: 'suspend' | 'activate' | 'change_plan') {
		bulkAction = action;
		bulkPlanId = '';
		showBulkDialog = true;
	}

	async function executeBulkAction() {
		if (!bulkAction || selectedUsers.size === 0) return;

		actionLoading = true;
		try {
			const result = await bulkUserAction(
				Array.from(selectedUsers),
				bulkAction,
				bulkAction === 'change_plan' ? bulkPlanId : undefined
			);
			toast.success(`${result.success_count} users updated, ${result.failure_count} failed`);
			showBulkDialog = false;
			selectedUsers = new Set();
			selectAll = false;
			await loadUsers();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : 'Bulk action failed');
		} finally {
			actionLoading = false;
		}
	}

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	function formatDate(date: string | null): string {
		if (!date) return 'Never';
		return new Intl.DateTimeFormat('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		}).format(new Date(date));
	}

	function getStatusBadge(
		user: AdminUser
	): { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string } {
		if (!user.is_active) {
			return { variant: 'destructive', label: 'Inactive' };
		}
		if (user.subscription_status === 'active') {
			return { variant: 'default', label: 'Active' };
		}
		return { variant: 'secondary', label: 'No Sub' };
	}

	function getPlanBadge(
		tier: string
	): 'default' | 'secondary' | 'destructive' | 'outline' {
		switch (tier) {
			case 'pro':
				return 'default';
			case 'enterprise':
				return 'destructive';
			default:
				return 'secondary';
		}
	}

	function getUserDisplayName(user: AdminUser): string {
		if (user.first_name && user.last_name) {
			return `${user.first_name} ${user.last_name}`;
		}
		if (user.first_name) return user.first_name;
		return user.username;
	}

	function getUsagePercentage(user: AdminUser): number {
		if (user.tokens_limit <= 0) return 0;
		return Math.min(100, (user.tokens_used / user.tokens_limit) * 100);
	}
</script>

<svelte:head>
	<title>Users - Admin - RAG Agent Platform</title>
</svelte:head>

<div class="p-6 space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-bold">Users</h1>
			<p class="text-muted-foreground mt-1">Manage user accounts and subscriptions</p>
		</div>
		<div class="text-sm text-muted-foreground">
			{totalUsers} total users
		</div>
	</div>

	<!-- Filters and Search -->
	<Card.Root>
		<Card.Content class="pt-6">
			<div class="flex flex-col md:flex-row gap-4">
				<!-- Search -->
				<div class="relative flex-1">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
					<Input
						placeholder="Search by email, name, or username..."
						class="pl-10"
						value={searchQuery}
						oninput={handleSearch}
					/>
				</div>

				<!-- Plan Filter -->
				<Select.Root type="single" value={planFilter} onValueChange={handlePlanFilterChange}>
					<Select.Trigger class="w-[180px]">
						{planFilter === 'all' ? 'All Plans' : plans.find((p) => p.plan_type === planFilter)?.display_name || planFilter}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="all">All Plans</Select.Item>
						<Select.Item value="free">Free</Select.Item>
						<Select.Item value="pro">Pro</Select.Item>
						<Select.Item value="enterprise">Enterprise</Select.Item>
					</Select.Content>
				</Select.Root>

				<!-- Status Filter -->
				<Select.Root type="single" value={statusFilter} onValueChange={handleStatusFilterChange}>
					<Select.Trigger class="w-[150px]">
						{statusFilter === 'all' ? 'All Status' : statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="all">All Status</Select.Item>
						<Select.Item value="active">Active</Select.Item>
						<Select.Item value="inactive">Inactive</Select.Item>
					</Select.Content>
				</Select.Root>
			</div>

			<!-- Bulk Actions -->
			{#if selectedUsers.size > 0}
				<div class="mt-4 flex items-center gap-4 p-3 bg-muted rounded-lg">
					<span class="text-sm font-medium">{selectedUsers.size} users selected</span>
					<div class="flex gap-2">
						<Button variant="outline" size="sm" onclick={() => openBulkDialog('change_plan')}>
							<CreditCard class="h-4 w-4 mr-1" />
							Change Plan
						</Button>
						<Button variant="outline" size="sm" onclick={() => openBulkDialog('suspend')}>
							<UserX class="h-4 w-4 mr-1" />
							Suspend
						</Button>
						<Button variant="outline" size="sm" onclick={() => openBulkDialog('activate')}>
							<UserCheck class="h-4 w-4 mr-1" />
							Activate
						</Button>
					</div>
					<Button
						variant="ghost"
						size="sm"
						onclick={() => {
							selectedUsers = new Set();
							selectAll = false;
						}}
					>
						Clear Selection
					</Button>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>

	<!-- Users Table -->
	{#if loading}
		<Card.Root>
			<Card.Content class="pt-6">
				<div class="space-y-4">
					{#each Array(5) as _}
						<div class="flex items-center gap-4">
							<Skeleton class="h-4 w-4" />
							<Skeleton class="h-10 w-10 rounded-full" />
							<div class="flex-1 space-y-2">
								<Skeleton class="h-4 w-48" />
								<Skeleton class="h-3 w-32" />
							</div>
							<Skeleton class="h-6 w-16" />
							<Skeleton class="h-6 w-20" />
							<Skeleton class="h-4 w-24" />
						</div>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>
	{:else if error}
		<Card.Root class="border-destructive">
			<Card.Content class="pt-6">
				<p class="text-destructive">{error}</p>
				<Button variant="outline" class="mt-4" onclick={loadUsers}>Retry</Button>
			</Card.Content>
		</Card.Root>
	{:else if users.length === 0}
		<Card.Root>
			<Card.Content class="flex flex-col items-center justify-center py-12">
				<Users class="h-12 w-12 text-muted-foreground mb-4" />
				<h3 class="text-lg font-medium">No users found</h3>
				<p class="text-muted-foreground text-sm mt-1">
					{searchQuery || planFilter !== 'all' || statusFilter !== 'all'
						? 'Try adjusting your filters'
						: 'No users have registered yet'}
				</p>
			</Card.Content>
		</Card.Root>
	{:else}
		<Card.Root>
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head class="w-12">
							<Checkbox checked={selectAll} onCheckedChange={toggleSelectAll} />
						</Table.Head>
						<Table.Head>User</Table.Head>
						<Table.Head>Plan</Table.Head>
						<Table.Head>Status</Table.Head>
						<Table.Head>Usage</Table.Head>
						<Table.Head>Revenue</Table.Head>
						<Table.Head>Last Active</Table.Head>
						<Table.Head class="w-12"></Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each users as user (user.id)}
						<Table.Row class={!user.is_active ? 'opacity-60' : ''}>
							<Table.Cell>
								<Checkbox
									checked={selectedUsers.has(user.id)}
									onCheckedChange={() => toggleUserSelection(user.id)}
								/>
							</Table.Cell>
							<Table.Cell>
								<div class="flex items-center gap-3">
									<div class="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
										<span class="text-sm font-medium text-primary">
											{user.email.charAt(0).toUpperCase()}
										</span>
									</div>
									<div>
										<p class="font-medium">{getUserDisplayName(user)}</p>
										<p class="text-sm text-muted-foreground">{user.email}</p>
									</div>
								</div>
							</Table.Cell>
							<Table.Cell>
								<Badge variant={getPlanBadge(user.tier)}>{user.tier}</Badge>
								{#if user.plan_name}
									<p class="text-xs text-muted-foreground mt-1">{user.plan_name}</p>
								{/if}
							</Table.Cell>
							<Table.Cell>
								{@const status = getStatusBadge(user)}
								<Badge variant={status.variant}>{status.label}</Badge>
							</Table.Cell>
							<Table.Cell>
								<div class="w-24">
									<Progress value={getUsagePercentage(user)} class="h-2" />
									<p class="text-xs text-muted-foreground mt-1">
										{user.tokens_used.toLocaleString()} / {user.tokens_limit.toLocaleString()}
									</p>
								</div>
							</Table.Cell>
							<Table.Cell>
								<span class="font-medium">{formatCurrency(user.revenue_total)}</span>
							</Table.Cell>
							<Table.Cell>
								<span class="text-sm text-muted-foreground">{formatDate(user.last_active)}</span>
							</Table.Cell>
							<Table.Cell>
								<DropdownMenu.Root>
									<DropdownMenu.Trigger>
										<Button variant="ghost" size="icon">
											<MoreHorizontal class="h-4 w-4" />
										</Button>
									</DropdownMenu.Trigger>
									<DropdownMenu.Content align="end">
										<DropdownMenu.Item onclick={() => openActionDialog(user, 'changePlan')}>
											<CreditCard class="h-4 w-4 mr-2" />
											Change Plan
										</DropdownMenu.Item>
										{#if user.is_active}
											<DropdownMenu.Item onclick={() => openActionDialog(user, 'suspend')}>
												<UserX class="h-4 w-4 mr-2" />
												Suspend
											</DropdownMenu.Item>
										{:else}
											<DropdownMenu.Item onclick={() => handleActivateUser(user)}>
												<UserCheck class="h-4 w-4 mr-2" />
												Activate
											</DropdownMenu.Item>
										{/if}
										<DropdownMenu.Separator />
										<DropdownMenu.Item
											class="text-destructive"
											onclick={() => openActionDialog(user, 'ban')}
										>
											<Ban class="h-4 w-4 mr-2" />
											Ban User
										</DropdownMenu.Item>
										<DropdownMenu.Item
											class="text-destructive"
											onclick={() => openActionDialog(user, 'delete')}
										>
											<Trash2 class="h-4 w-4 mr-2" />
											Delete User
										</DropdownMenu.Item>
									</DropdownMenu.Content>
								</DropdownMenu.Root>
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</Card.Root>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="flex items-center justify-between">
				<p class="text-sm text-muted-foreground">
					Showing {(page - 1) * perPage + 1} to {Math.min(page * perPage, totalUsers)} of {totalUsers} users
				</p>
				<div class="flex items-center gap-2">
					<Button
						variant="outline"
						size="sm"
						disabled={page === 1}
						onclick={() => {
							page--;
							loadUsers();
						}}
					>
						<ChevronLeft class="h-4 w-4" />
						Previous
					</Button>
					<span class="text-sm">
						Page {page} of {totalPages}
					</span>
					<Button
						variant="outline"
						size="sm"
						disabled={page === totalPages}
						onclick={() => {
							page++;
							loadUsers();
						}}
					>
						Next
						<ChevronRight class="h-4 w-4" />
					</Button>
				</div>
			</div>
		{/if}
	{/if}
</div>

<!-- Action Confirmation Dialog -->
<AlertDialog.Root open={actionUser !== null && actionType !== null}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>
				{#if actionType === 'suspend'}
					Suspend User
				{:else if actionType === 'ban'}
					Ban User
				{:else if actionType === 'delete'}
					Delete User
				{:else if actionType === 'changePlan'}
					Change User Plan
				{/if}
			</AlertDialog.Title>
			<AlertDialog.Description>
				{#if actionType === 'suspend'}
					Are you sure you want to suspend "{actionUser?.email}"? They will lose access to their account.
				{:else if actionType === 'ban'}
					Are you sure you want to ban "{actionUser?.email}"? This action is severe and should only be used for policy violations.
				{:else if actionType === 'delete'}
					Are you sure you want to delete "{actionUser?.email}"? This will permanently delete all their data. This action cannot be undone.
				{:else if actionType === 'changePlan'}
					Select a new plan for "{actionUser?.email}".
				{/if}
			</AlertDialog.Description>
		</AlertDialog.Header>

		{#if actionType === 'changePlan'}
			<div class="py-4">
				<Select.Root type="single" value={selectedPlanId} onValueChange={(v) => selectedPlanId = v || ''}>
					<Select.Trigger>
						{plans.find((p) => p.id === selectedPlanId)?.display_name || 'Select a plan'}
					</Select.Trigger>
					<Select.Content>
						{#each plans as plan}
							<Select.Item value={plan.id}>{plan.display_name}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
		{:else if actionType === 'suspend' || actionType === 'ban'}
			<div class="py-4">
				<Input
					placeholder="Reason (optional)"
					bind:value={actionReason}
				/>
			</div>
		{/if}

		<AlertDialog.Footer>
			<AlertDialog.Cancel onclick={closeActionDialog}>Cancel</AlertDialog.Cancel>
			<AlertDialog.Action
				onclick={executeAction}
				disabled={actionLoading || (actionType === 'changePlan' && !selectedPlanId)}
				class={actionType === 'delete' || actionType === 'ban' ? 'bg-destructive text-destructive-foreground hover:bg-destructive/90' : ''}
			>
				{actionLoading ? 'Processing...' : 'Confirm'}
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>

<!-- Bulk Action Dialog -->
<AlertDialog.Root open={showBulkDialog}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>
				{#if bulkAction === 'change_plan'}
					Change Plan for {selectedUsers.size} Users
				{:else if bulkAction === 'suspend'}
					Suspend {selectedUsers.size} Users
				{:else if bulkAction === 'activate'}
					Activate {selectedUsers.size} Users
				{/if}
			</AlertDialog.Title>
			<AlertDialog.Description>
				This action will be applied to all selected users.
			</AlertDialog.Description>
		</AlertDialog.Header>

		{#if bulkAction === 'change_plan'}
			<div class="py-4">
				<Select.Root type="single" value={bulkPlanId} onValueChange={(v) => bulkPlanId = v || ''}>
					<Select.Trigger>
						{plans.find((p) => p.id === bulkPlanId)?.display_name || 'Select a plan'}
					</Select.Trigger>
					<Select.Content>
						{#each plans as plan}
							<Select.Item value={plan.id}>{plan.display_name}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
		{/if}

		<AlertDialog.Footer>
			<AlertDialog.Cancel onclick={() => (showBulkDialog = false)}>Cancel</AlertDialog.Cancel>
			<AlertDialog.Action
				onclick={executeBulkAction}
				disabled={actionLoading || (bulkAction === 'change_plan' && !bulkPlanId)}
			>
				{actionLoading ? 'Processing...' : 'Confirm'}
			</AlertDialog.Action>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
