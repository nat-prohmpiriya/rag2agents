<script lang="ts">
	import { onMount } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Progress } from '$lib/components/ui/progress';
	import * as Card from '$lib/components/ui/card';
	import { Separator } from '$lib/components/ui/separator';
	import { getPlans, createCheckout, createPortalSession, type BillingPlan } from '$lib/api/billing';
	import { profileApi, type UserUsage } from '$lib/api/profile';
	import {
		CreditCard,
		Zap,
		FileText,
		ExternalLink,
		ArrowUpRight,
		Calendar,
		Loader2,
		AlertCircle,
		CheckCircle,
		Clock,
		Sparkles
	} from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { auth } from '$lib/stores';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let usage = $state<UserUsage | null>(null);
	let plans = $state<BillingPlan[]>([]);
	let currentPlan = $state<BillingPlan | null>(null);
	let portalLoading = $state(false);
	let upgradeLoading = $state<string | null>(null);

	// Get user tier from auth store
	let userTier = $derived(auth.user?.tier || 'free');

	onMount(async () => {
		await loadData();
	});

	async function loadData() {
		loading = true;
		error = null;

		try {
			const [usageData, plansData] = await Promise.all([
				profileApi.getUsage(),
				getPlans()
			]);

			usage = usageData;
			plans = plansData;

			// Find current plan based on user tier
			currentPlan = plans.find(p => p.plan_type === userTier) || plans.find(p => p.plan_type === 'free') || null;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load billing data';
		} finally {
			loading = false;
		}
	}

	async function openCustomerPortal() {
		portalLoading = true;
		try {
			const response = await createPortalSession(window.location.href);
			window.location.href = response.url;
		} catch (e) {
			toast.error(e instanceof Error ? e.message : 'Failed to open billing portal');
			portalLoading = false;
		}
	}

	async function handleUpgrade(plan: BillingPlan) {
		if (plan.plan_type === 'enterprise') {
			window.location.href = '/contact';
			return;
		}

		upgradeLoading = plan.id;
		try {
			const baseUrl = window.location.origin;
			const response = await createCheckout({
				plan_id: plan.id,
				billing_interval: 'monthly',
				success_url: `${baseUrl}/billing/success?session_id={CHECKOUT_SESSION_ID}`,
				cancel_url: `${baseUrl}/settings/billing`
			});
			window.location.href = response.url;
		} catch (e) {
			toast.error(e instanceof Error ? e.message : 'Failed to create checkout session');
			upgradeLoading = null;
		}
	}

	function formatCurrency(amount: number, currency: string = 'USD'): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency,
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	function formatNumber(num: number): string {
		if (num >= 1000000) {
			return `${(num / 1000000).toFixed(1)}M`;
		}
		if (num >= 1000) {
			return `${(num / 1000).toFixed(0)}K`;
		}
		return num.toString();
	}

	function getStatusBadge(tier: string): { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string } {
		switch (tier) {
			case 'pro':
				return { variant: 'default', label: 'Pro' };
			case 'enterprise':
				return { variant: 'destructive', label: 'Enterprise' };
			default:
				return { variant: 'secondary', label: 'Free' };
		}
	}

	function isUpgrade(plan: BillingPlan): boolean {
		const tierOrder = { free: 0, pro: 1, enterprise: 2 };
		return tierOrder[plan.plan_type] > tierOrder[userTier as keyof typeof tierOrder];
	}
</script>

<svelte:head>
	<title>Billing & Subscription | RAG Agent</title>
</svelte:head>

<div class="flex h-full flex-col">
	<div class="flex-1 overflow-auto p-8">
		<div class="mx-auto max-w-4xl space-y-6">
			<!-- Header -->
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<CreditCard class="size-8 text-foreground" />
					<div>
						<h1 class="text-3xl font-semibold text-foreground">Billing & Subscription</h1>
						<p class="text-sm text-muted-foreground mt-1">
							Manage your subscription and billing information
						</p>
					</div>
				</div>
				{#if userTier !== 'free'}
					<Button onclick={openCustomerPortal} disabled={portalLoading} variant="outline">
						{#if portalLoading}
							<Loader2 class="size-4 animate-spin mr-2" />
						{:else}
							<ExternalLink class="size-4 mr-2" />
						{/if}
						Manage Billing
					</Button>
				{/if}
			</div>

			{#if error}
				<div class="rounded-md bg-destructive/10 p-4 text-destructive text-sm flex items-center gap-2">
					<AlertCircle class="size-4" />
					{error}
				</div>
			{/if}

			{#if loading}
				<div class="space-y-6">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="space-y-4">
								<Skeleton class="h-6 w-32" />
								<Skeleton class="h-4 w-48" />
								<Skeleton class="h-2 w-full" />
							</div>
						</Card.Content>
					</Card.Root>
				</div>
			{:else}
				<!-- Current Plan -->
				<Card.Root>
					<Card.Header>
						<div class="flex items-center justify-between">
							<div>
								<Card.Title class="flex items-center gap-2">
									Current Plan
									{@const status = getStatusBadge(userTier)}
									<Badge variant={status.variant}>{status.label}</Badge>
								</Card.Title>
								<Card.Description>
									{#if currentPlan}
										{currentPlan.display_name} - {currentPlan.description || 'Your current subscription plan'}
									{:else}
										Free tier with limited features
									{/if}
								</Card.Description>
							</div>
							{#if currentPlan && currentPlan.plan_type !== 'free'}
								<div class="text-right">
									<p class="text-2xl font-bold">{formatCurrency(currentPlan.price_monthly)}</p>
									<p class="text-sm text-muted-foreground">/month</p>
								</div>
							{/if}
						</div>
					</Card.Header>
					{#if currentPlan}
						<Card.Content>
							<div class="grid gap-4 md:grid-cols-3">
								<div class="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
									<Zap class="size-5 text-primary" />
									<div>
										<p class="text-sm font-medium">{formatNumber(currentPlan.tokens_per_month)}</p>
										<p class="text-xs text-muted-foreground">Tokens/month</p>
									</div>
								</div>
								<div class="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
									<FileText class="size-5 text-primary" />
									<div>
										<p class="text-sm font-medium">{currentPlan.max_documents}</p>
										<p class="text-xs text-muted-foreground">Documents</p>
									</div>
								</div>
								<div class="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
									<Sparkles class="size-5 text-primary" />
									<div>
										<p class="text-sm font-medium">{currentPlan.max_agents}</p>
										<p class="text-xs text-muted-foreground">AI Agents</p>
									</div>
								</div>
							</div>
						</Card.Content>
					{/if}
				</Card.Root>

				<!-- Usage -->
				{#if usage}
					<Card.Root>
						<Card.Header>
							<Card.Title>Usage This Month</Card.Title>
							<Card.Description>Your token usage resets at the beginning of each billing cycle</Card.Description>
						</Card.Header>
						<Card.Content class="space-y-6">
							<!-- Token Usage -->
							<div class="space-y-2">
								<div class="flex items-center justify-between text-sm">
									<span class="font-medium">Tokens Used</span>
									<span class="text-muted-foreground">
										{formatNumber(usage.tokens_this_month)}
										{#if usage.quota}
											/ {formatNumber(usage.quota.tokens_limit)}
										{/if}
									</span>
								</div>
								{#if usage.quota}
									<Progress value={usage.quota.percentage} class="h-2" />
									<p class="text-xs text-muted-foreground">
										{usage.quota.percentage}% used
										{#if usage.quota.percentage >= 80}
											<span class="text-yellow-500"> - Consider upgrading for more tokens</span>
										{/if}
									</p>
								{/if}
							</div>

							<Separator />

							<!-- Stats -->
							<div class="grid gap-4 md:grid-cols-3">
								<div>
									<p class="text-sm text-muted-foreground">Messages This Month</p>
									<p class="text-xl font-semibold">{usage.messages_this_month.toLocaleString()}</p>
								</div>
								<div>
									<p class="text-sm text-muted-foreground">Cost This Month</p>
									<p class="text-xl font-semibold">${usage.cost_this_month.toFixed(2)}</p>
								</div>
								<div>
									<p class="text-sm text-muted-foreground">Total Cost (All Time)</p>
									<p class="text-xl font-semibold">${usage.estimated_cost.toFixed(2)}</p>
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				{/if}

				<!-- Upgrade Plans -->
				{#if plans.filter(p => isUpgrade(p)).length > 0}
					<Card.Root>
						<Card.Header>
							<Card.Title>Upgrade Your Plan</Card.Title>
							<Card.Description>Get more tokens, documents, and features</Card.Description>
						</Card.Header>
						<Card.Content>
							<div class="grid gap-4 md:grid-cols-2">
								{#each plans.filter(p => isUpgrade(p)) as plan (plan.id)}
									<div class="relative p-6 rounded-lg border-2 {plan.plan_type === 'pro' ? 'border-primary bg-primary/5' : 'border-border'}">
										{#if plan.plan_type === 'pro'}
											<div class="absolute -top-3 left-4">
												<Badge class="bg-primary text-primary-foreground">
													<Sparkles class="size-3 mr-1" />
													Popular
												</Badge>
											</div>
										{/if}

										<div class="mb-4">
											<h3 class="font-semibold text-lg">{plan.display_name}</h3>
											<p class="text-sm text-muted-foreground">{plan.description}</p>
										</div>

										<div class="mb-4">
											{#if plan.plan_type === 'enterprise'}
												<p class="text-2xl font-bold">Custom</p>
												<p class="text-sm text-muted-foreground">Contact us for pricing</p>
											{:else}
												<p class="text-2xl font-bold">{formatCurrency(plan.price_monthly)}<span class="text-sm font-normal text-muted-foreground">/month</span></p>
												{#if plan.price_yearly}
													<p class="text-sm text-muted-foreground">or {formatCurrency(plan.price_yearly)}/year (save 20%)</p>
												{/if}
											{/if}
										</div>

										<ul class="space-y-2 mb-6 text-sm">
											<li class="flex items-center gap-2">
												<CheckCircle class="size-4 text-green-500" />
												{formatNumber(plan.tokens_per_month)} tokens/month
											</li>
											<li class="flex items-center gap-2">
												<CheckCircle class="size-4 text-green-500" />
												{plan.max_documents} documents
											</li>
											<li class="flex items-center gap-2">
												<CheckCircle class="size-4 text-green-500" />
												{plan.max_agents} AI agents
											</li>
											<li class="flex items-center gap-2">
												<CheckCircle class="size-4 text-green-500" />
												{plan.allowed_models.length} AI models
											</li>
										</ul>

										<Button
											onclick={() => handleUpgrade(plan)}
											disabled={upgradeLoading !== null}
											class="w-full"
											variant={plan.plan_type === 'pro' ? 'default' : 'outline'}
										>
											{#if upgradeLoading === plan.id}
												<Loader2 class="size-4 animate-spin mr-2" />
												Processing...
											{:else}
												<ArrowUpRight class="size-4 mr-2" />
												{plan.plan_type === 'enterprise' ? 'Contact Sales' : 'Upgrade Now'}
											{/if}
										</Button>
									</div>
								{/each}
							</div>
						</Card.Content>
					</Card.Root>
				{/if}

				<!-- Billing Portal Info -->
				{#if userTier !== 'free'}
					<Card.Root>
						<Card.Header>
							<Card.Title>Billing Management</Card.Title>
							<Card.Description>Manage your subscription through our secure billing portal</Card.Description>
						</Card.Header>
						<Card.Content>
							<div class="flex flex-col sm:flex-row gap-4">
								<div class="flex-1 p-4 rounded-lg bg-muted/50">
									<div class="flex items-center gap-2 mb-2">
										<CreditCard class="size-4 text-muted-foreground" />
										<span class="font-medium">Payment Methods</span>
									</div>
									<p class="text-sm text-muted-foreground">Update your credit card or payment method</p>
								</div>
								<div class="flex-1 p-4 rounded-lg bg-muted/50">
									<div class="flex items-center gap-2 mb-2">
										<FileText class="size-4 text-muted-foreground" />
										<span class="font-medium">Invoice History</span>
									</div>
									<p class="text-sm text-muted-foreground">View and download past invoices</p>
								</div>
								<div class="flex-1 p-4 rounded-lg bg-muted/50">
									<div class="flex items-center gap-2 mb-2">
										<Calendar class="size-4 text-muted-foreground" />
										<span class="font-medium">Subscription</span>
									</div>
									<p class="text-sm text-muted-foreground">Change plan or cancel subscription</p>
								</div>
							</div>
							<Button onclick={openCustomerPortal} disabled={portalLoading} class="mt-4">
								{#if portalLoading}
									<Loader2 class="size-4 animate-spin mr-2" />
								{:else}
									<ExternalLink class="size-4 mr-2" />
								{/if}
								Open Billing Portal
							</Button>
						</Card.Content>
					</Card.Root>
				{:else}
					<!-- Free Plan Info -->
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="text-center py-6">
								<div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-muted mb-4">
									<CreditCard class="size-6 text-muted-foreground" />
								</div>
								<h3 class="font-semibold mb-2">You're on the Free Plan</h3>
								<p class="text-sm text-muted-foreground mb-4">
									Upgrade to Pro for more tokens, documents, and advanced features.
								</p>
								<Button href="/pricing">
									View Pricing Plans
									<ArrowUpRight class="size-4 ml-2" />
								</Button>
							</div>
						</Card.Content>
					</Card.Root>
				{/if}
			{/if}
		</div>
	</div>
</div>
