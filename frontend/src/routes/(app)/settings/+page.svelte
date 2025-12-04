<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import * as Tabs from '$lib/components/ui/tabs';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { User, BarChart3, CreditCard, Settings2, Settings } from 'lucide-svelte';
	import { profileApi, type UserProfile, type UserStats, type UserUsage } from '$lib/api';
	import { getPlans, type BillingPlan } from '$lib/api/billing';
	import { auth } from '$lib/stores';

	// Tab components
	import AccountTab from '$lib/components/settings/AccountTab.svelte';
	import UsageTab from '$lib/components/profile/UsageTab.svelte';
	import BillingTab from '$lib/components/settings/BillingTab.svelte';
	import ConfigTab from '$lib/components/settings/ConfigTab.svelte';

	// State
	let loading = $state(true);
	let error = $state<string | null>(null);
	let profile = $state<UserProfile | null>(null);
	let stats = $state<UserStats | null>(null);
	let usage = $state<UserUsage | null>(null);
	let plans = $state<BillingPlan[]>([]);

	// Get initial tab from URL or default
	let activeTab = $state('account');

	// Tab definitions
	const tabs = [
		{ id: 'account', label: 'Account', icon: User },
		{ id: 'usage', label: 'Usage', icon: BarChart3 },
		{ id: 'billing', label: 'Billing', icon: CreditCard },
		{ id: 'config', label: 'Config', icon: Settings2 }
	];

	onMount(async () => {
		// Check URL for initial tab
		const tabParam = $page.url.searchParams.get('tab');
		if (tabParam && tabs.some(t => t.id === tabParam)) {
			activeTab = tabParam;
		}

		await loadData();
	});

	async function loadData() {
		loading = true;
		error = null;

		try {
			const [profileData, statsData, usageData, plansData] = await Promise.all([
				profileApi.getProfile(),
				profileApi.getStats(),
				profileApi.getUsage(),
				getPlans()
			]);

			profile = profileData;
			stats = statsData;
			usage = usageData;
			plans = plansData;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings data';
		} finally {
			loading = false;
		}
	}

	function handleTabChange(value: string) {
		activeTab = value;
		// Update URL without reload
		const url = new URL(window.location.href);
		url.searchParams.set('tab', value);
		window.history.replaceState({}, '', url.toString());
	}

	function handleProfileUpdate(updatedProfile: UserProfile) {
		profile = updatedProfile;
	}
</script>

<svelte:head>
	<title>Settings | RAG Agent Platform</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-6xl">
			<!-- Header -->
			<div class="flex items-center gap-3 mb-6">
				<Settings class="size-8 text-foreground" />
				<h1 class="text-3xl font-semibold text-foreground">Settings</h1>
			</div>

			{#if error}
				<div class="rounded-md bg-destructive/10 p-4 text-destructive text-sm mb-6">
					{error}
				</div>
			{/if}

			{#if loading}
				<div class="space-y-4">
					<Skeleton class="h-10 w-full max-w-md" />
					<Skeleton class="h-64 w-full" />
				</div>
			{:else}
				<Tabs.Root value={activeTab} onValueChange={handleTabChange} class="w-full">
					<Tabs.List class="mb-6 inline-flex h-11 items-center justify-start gap-1 rounded-lg bg-muted p-1">
						{#each tabs as tab}
							{@const Icon = tab.icon}
							<Tabs.Trigger
								value={tab.id}
								class="inline-flex items-center justify-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 hover:text-foreground data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
							>
								<Icon class="size-4 mr-2" />
								{tab.label}
							</Tabs.Trigger>
						{/each}
					</Tabs.List>

					<Tabs.Content value="account" class="mt-0">
						{#if profile}
							<AccountTab
								{profile}
								{stats}
								onProfileUpdate={handleProfileUpdate}
							/>
						{/if}
					</Tabs.Content>

					<Tabs.Content value="usage" class="mt-0">
						<UsageTab {usage} {stats} loading={false} />
					</Tabs.Content>

					<Tabs.Content value="billing" class="mt-0">
						<BillingTab {usage} {plans} />
					</Tabs.Content>

					<Tabs.Content value="config" class="mt-0">
						<ConfigTab />
					</Tabs.Content>
				</Tabs.Root>
			{/if}
		</div>
	</div>
</div>
