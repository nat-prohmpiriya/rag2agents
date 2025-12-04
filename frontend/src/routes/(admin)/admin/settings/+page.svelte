<script lang="ts">
	import { onMount } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Switch } from '$lib/components/ui/switch';
	import * as Select from '$lib/components/ui/select';
	import * as Tabs from '$lib/components/ui/tabs';
	import { Badge } from '$lib/components/ui/badge';
	import {
		Settings,
		CreditCard,
		Zap,
		Bell,
		Save,
		RefreshCw,
		Eye,
		EyeOff,
		Loader2
	} from 'lucide-svelte';
	import {
		getAllSettings,
		updateAllSettings,
		initializeSettings,
		getPlans,
		type AllSettings,
		type GeneralSettings,
		type PaymentSettings,
		type LiteLLMSettings,
		type NotificationSettings,
		type Plan
	} from '$lib/api/admin';

	let settings = $state<AllSettings | null>(null);
	let plans = $state<Plan[]>([]);
	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let successMessage = $state<string | null>(null);
	let activeTab = $state('general');

	// Track which secrets are visible
	let visibleSecrets = $state<Record<string, boolean>>({});

	// Form state - create separate mutable copies
	let generalForm = $state<GeneralSettings>({
		site_name: 'RAG Agent Platform',
		default_plan_id: null,
		trial_period_days: 14,
		allow_registration: true,
		require_email_verification: true
	});

	let paymentForm = $state<PaymentSettings>({
		stripe_publishable_key: null,
		stripe_secret_key: null,
		stripe_webhook_secret: null,
		currency: 'usd',
		tax_rate_percent: 0.0
	});

	let litellmForm = $state<LiteLLMSettings>({
		proxy_url: null,
		master_key: null,
		default_model: 'gemini-2.0-flash',
		fallback_model: null,
		request_timeout_seconds: 60
	});

	let notificationForm = $state<NotificationSettings>({
		slack_webhook_url: null,
		email_enabled: true,
		email_from_name: 'RAG Agent Platform',
		email_from_address: null,
		smtp_host: null,
		smtp_port: 587,
		smtp_username: null,
		smtp_password: null,
		smtp_use_tls: true
	});

	onMount(async () => {
		await loadSettings();
		await loadPlans();
	});

	async function loadSettings() {
		try {
			loading = true;
			error = null;
			settings = await getAllSettings();
			// Copy to form state
			if (settings) {
				generalForm = { ...settings.general };
				paymentForm = { ...settings.payment };
				litellmForm = { ...settings.litellm };
				notificationForm = { ...settings.notification };
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load settings';
			// Initialize default settings if not found
			if (error.includes('404') || error.includes('not found')) {
				await handleInitialize();
			}
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

	async function handleInitialize() {
		try {
			loading = true;
			await initializeSettings();
			await loadSettings();
			successMessage = 'Settings initialized successfully';
			setTimeout(() => (successMessage = null), 3000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to initialize settings';
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		try {
			saving = true;
			error = null;

			const updateData: Record<string, unknown> = {};

			// Only include sections that have changed
			if (activeTab === 'general' || activeTab === 'all') {
				updateData.general = generalForm;
			}
			if (activeTab === 'payment' || activeTab === 'all') {
				updateData.payment = paymentForm;
			}
			if (activeTab === 'litellm' || activeTab === 'all') {
				updateData.litellm = litellmForm;
			}
			if (activeTab === 'notification' || activeTab === 'all') {
				updateData.notification = notificationForm;
			}

			settings = await updateAllSettings(updateData);

			// Update form with response (in case secrets were masked)
			if (settings) {
				generalForm = { ...settings.general };
				paymentForm = { ...settings.payment };
				litellmForm = { ...settings.litellm };
				notificationForm = { ...settings.notification };
			}

			successMessage = 'Settings saved successfully';
			setTimeout(() => (successMessage = null), 3000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save settings';
		} finally {
			saving = false;
		}
	}

	function toggleSecretVisibility(key: string) {
		visibleSecrets[key] = !visibleSecrets[key];
	}

	function isSecretMasked(value: string | null): boolean {
		return value?.includes('*') ?? false;
	}

	const currencyOptions = [
		{ value: 'usd', label: 'USD ($)' },
		{ value: 'eur', label: 'EUR (&euro;)' },
		{ value: 'gbp', label: 'GBP (&pound;)' },
		{ value: 'jpy', label: 'JPY (&yen;)' },
		{ value: 'thb', label: 'THB (&curren;)' }
	];

	const modelOptions = [
		{ value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
		{ value: 'gemini-2.0-pro', label: 'Gemini 2.0 Pro' },
		{ value: 'llama-3.3-70b', label: 'Llama 3.3 70B' },
		{ value: 'claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
		{ value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
		{ value: 'gpt-4o', label: 'GPT-4o' }
	];
</script>

<svelte:head>
	<title>Settings | Admin</title>
</svelte:head>

<div class="flex-1 space-y-6 p-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold">Settings</h1>
			<p class="text-muted-foreground">Configure application settings</p>
		</div>
		<div class="flex items-center gap-2">
			<Button variant="outline" onclick={loadSettings} disabled={loading}>
				<RefreshCw class="mr-2 h-4 w-4 {loading ? 'animate-spin' : ''}" />
				Refresh
			</Button>
			<Button onclick={handleSave} disabled={saving || loading}>
				{#if saving}
					<Loader2 class="mr-2 h-4 w-4 animate-spin" />
				{:else}
					<Save class="mr-2 h-4 w-4" />
				{/if}
				Save Changes
			</Button>
		</div>
	</div>

	<!-- Messages -->
	{#if error}
		<div class="rounded-md bg-destructive/10 p-4 text-destructive">
			{error}
		</div>
	{/if}

	{#if successMessage}
		<div class="rounded-md bg-green-500/10 p-4 text-green-600 dark:text-green-400">
			{successMessage}
		</div>
	{/if}

	{#if loading && !settings}
		<div class="flex items-center justify-center py-12">
			<div class="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent">
			</div>
		</div>
	{:else}
		<Tabs.Root value={activeTab} onValueChange={(v) => (activeTab = v || 'general')}>
			<Tabs.List class="grid w-full grid-cols-4">
				<Tabs.Trigger value="general" class="flex items-center gap-2">
					<Settings class="h-4 w-4" />
					General
				</Tabs.Trigger>
				<Tabs.Trigger value="payment" class="flex items-center gap-2">
					<CreditCard class="h-4 w-4" />
					Payment
				</Tabs.Trigger>
				<Tabs.Trigger value="litellm" class="flex items-center gap-2">
					<Zap class="h-4 w-4" />
					LiteLLM
				</Tabs.Trigger>
				<Tabs.Trigger value="notification" class="flex items-center gap-2">
					<Bell class="h-4 w-4" />
					Notifications
				</Tabs.Trigger>
			</Tabs.List>

			<!-- General Settings -->
			<Tabs.Content value="general" class="mt-6">
				<Card.Root>
					<Card.Header>
						<Card.Title>General Settings</Card.Title>
						<Card.Description>Configure general application settings</Card.Description>
					</Card.Header>
					<Card.Content class="space-y-6">
						<div class="space-y-2">
							<Label for="site_name">Site Name</Label>
							<Input
								id="site_name"
								bind:value={generalForm.site_name}
								placeholder="RAG Agent Platform"
							/>
							<p class="text-xs text-muted-foreground">The name displayed throughout the application</p>
						</div>

						<div class="space-y-2">
							<Label for="default_plan">Default Plan</Label>
							<Select.Root
								type="single"
								value={generalForm.default_plan_id || undefined}
								onValueChange={(v) => {
									generalForm.default_plan_id = v || null;
								}}
							>
								<Select.Trigger id="default_plan" class="w-full">
									{#if generalForm.default_plan_id}
										{plans.find((p) => p.id === generalForm.default_plan_id)?.display_name ||
											'Select plan'}
									{:else}
										Select default plan
									{/if}
								</Select.Trigger>
								<Select.Content>
									{#each plans as plan}
										<Select.Item value={plan.id}>
											{plan.display_name}
										</Select.Item>
									{/each}
								</Select.Content>
							</Select.Root>
							<p class="text-xs text-muted-foreground">Default plan for new users</p>
						</div>

						<div class="space-y-2">
							<Label for="trial_days">Trial Period (days)</Label>
							<Input
								id="trial_days"
								type="number"
								bind:value={generalForm.trial_period_days}
								min="0"
								max="90"
							/>
							<p class="text-xs text-muted-foreground">Number of days for trial period (0 to disable)</p>
						</div>

						<div class="flex items-center justify-between rounded-lg border p-4">
							<div class="space-y-0.5">
								<Label>Allow Registration</Label>
								<p class="text-sm text-muted-foreground">Allow new users to register</p>
							</div>
							<Switch bind:checked={generalForm.allow_registration} />
						</div>

						<div class="flex items-center justify-between rounded-lg border p-4">
							<div class="space-y-0.5">
								<Label>Require Email Verification</Label>
								<p class="text-sm text-muted-foreground">
									Require email verification for new accounts
								</p>
							</div>
							<Switch bind:checked={generalForm.require_email_verification} />
						</div>
					</Card.Content>
				</Card.Root>
			</Tabs.Content>

			<!-- Payment Settings -->
			<Tabs.Content value="payment" class="mt-6">
				<Card.Root>
					<Card.Header>
						<Card.Title>Payment Settings</Card.Title>
						<Card.Description>Configure Stripe and payment settings</Card.Description>
					</Card.Header>
					<Card.Content class="space-y-6">
						<div class="space-y-2">
							<Label for="stripe_publishable">Stripe Publishable Key</Label>
							<Input
								id="stripe_publishable"
								bind:value={paymentForm.stripe_publishable_key}
								placeholder="pk_live_..."
							/>
							<p class="text-xs text-muted-foreground">Public key for Stripe.js</p>
						</div>

						<div class="space-y-2">
							<Label for="stripe_secret">Stripe Secret Key</Label>
							<div class="flex gap-2">
								<Input
									id="stripe_secret"
									type={visibleSecrets['stripe_secret'] ? 'text' : 'password'}
									bind:value={paymentForm.stripe_secret_key}
									placeholder="sk_live_..."
									class="flex-1"
								/>
								<Button
									variant="outline"
									size="icon"
									onclick={() => toggleSecretVisibility('stripe_secret')}
								>
									{#if visibleSecrets['stripe_secret']}
										<EyeOff class="h-4 w-4" />
									{:else}
										<Eye class="h-4 w-4" />
									{/if}
								</Button>
							</div>
							{#if isSecretMasked(paymentForm.stripe_secret_key)}
								<Badge variant="secondary" class="text-xs">Masked - enter new value to update</Badge>
							{/if}
							<p class="text-xs text-muted-foreground">Secret key for server-side Stripe API calls</p>
						</div>

						<div class="space-y-2">
							<Label for="stripe_webhook">Stripe Webhook Secret</Label>
							<div class="flex gap-2">
								<Input
									id="stripe_webhook"
									type={visibleSecrets['stripe_webhook'] ? 'text' : 'password'}
									bind:value={paymentForm.stripe_webhook_secret}
									placeholder="whsec_..."
									class="flex-1"
								/>
								<Button
									variant="outline"
									size="icon"
									onclick={() => toggleSecretVisibility('stripe_webhook')}
								>
									{#if visibleSecrets['stripe_webhook']}
										<EyeOff class="h-4 w-4" />
									{:else}
										<Eye class="h-4 w-4" />
									{/if}
								</Button>
							</div>
							{#if isSecretMasked(paymentForm.stripe_webhook_secret)}
								<Badge variant="secondary" class="text-xs">Masked - enter new value to update</Badge>
							{/if}
							<p class="text-xs text-muted-foreground">Webhook signing secret for verifying Stripe events</p>
						</div>

						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<Label for="currency">Currency</Label>
								<Select.Root
									type="single"
									value={paymentForm.currency}
									onValueChange={(v) => {
										paymentForm.currency = v || 'usd';
									}}
								>
									<Select.Trigger id="currency">
										{currencyOptions.find((c) => c.value === paymentForm.currency)?.label || 'USD'}
									</Select.Trigger>
									<Select.Content>
										{#each currencyOptions as currency}
											<Select.Item value={currency.value}>{currency.label}</Select.Item>
										{/each}
									</Select.Content>
								</Select.Root>
							</div>

							<div class="space-y-2">
								<Label for="tax_rate">Tax Rate (%)</Label>
								<Input
									id="tax_rate"
									type="number"
									bind:value={paymentForm.tax_rate_percent}
									min="0"
									max="100"
									step="0.01"
								/>
							</div>
						</div>
					</Card.Content>
				</Card.Root>
			</Tabs.Content>

			<!-- LiteLLM Settings -->
			<Tabs.Content value="litellm" class="mt-6">
				<Card.Root>
					<Card.Header>
						<Card.Title>LiteLLM Settings</Card.Title>
						<Card.Description>Configure LiteLLM proxy connection</Card.Description>
					</Card.Header>
					<Card.Content class="space-y-6">
						<div class="space-y-2">
							<Label for="proxy_url">Proxy URL</Label>
							<Input
								id="proxy_url"
								bind:value={litellmForm.proxy_url}
								placeholder="http://localhost:4000"
							/>
							<p class="text-xs text-muted-foreground">LiteLLM proxy base URL</p>
						</div>

						<div class="space-y-2">
							<Label for="master_key">Master Key</Label>
							<div class="flex gap-2">
								<Input
									id="master_key"
									type={visibleSecrets['master_key'] ? 'text' : 'password'}
									bind:value={litellmForm.master_key}
									placeholder="sk-..."
									class="flex-1"
								/>
								<Button
									variant="outline"
									size="icon"
									onclick={() => toggleSecretVisibility('master_key')}
								>
									{#if visibleSecrets['master_key']}
										<EyeOff class="h-4 w-4" />
									{:else}
										<Eye class="h-4 w-4" />
									{/if}
								</Button>
							</div>
							{#if isSecretMasked(litellmForm.master_key)}
								<Badge variant="secondary" class="text-xs">Masked - enter new value to update</Badge>
							{/if}
							<p class="text-xs text-muted-foreground">LiteLLM master API key for admin operations</p>
						</div>

						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<Label for="default_model">Default Model</Label>
								<Select.Root
									type="single"
									value={litellmForm.default_model}
									onValueChange={(v) => {
										litellmForm.default_model = v || 'gemini-2.0-flash';
									}}
								>
									<Select.Trigger id="default_model">
										{modelOptions.find((m) => m.value === litellmForm.default_model)?.label ||
											litellmForm.default_model}
									</Select.Trigger>
									<Select.Content>
										{#each modelOptions as model}
											<Select.Item value={model.value}>{model.label}</Select.Item>
										{/each}
									</Select.Content>
								</Select.Root>
							</div>

							<div class="space-y-2">
								<Label for="fallback_model">Fallback Model</Label>
								<Select.Root
									type="single"
									value={litellmForm.fallback_model || undefined}
									onValueChange={(v) => {
										litellmForm.fallback_model = v || null;
									}}
								>
									<Select.Trigger id="fallback_model">
										{litellmForm.fallback_model
											? modelOptions.find((m) => m.value === litellmForm.fallback_model)?.label ||
												litellmForm.fallback_model
											: 'None'}
									</Select.Trigger>
									<Select.Content>
										<Select.Item value="">None</Select.Item>
										{#each modelOptions as model}
											<Select.Item value={model.value}>{model.label}</Select.Item>
										{/each}
									</Select.Content>
								</Select.Root>
							</div>
						</div>

						<div class="space-y-2">
							<Label for="timeout">Request Timeout (seconds)</Label>
							<Input
								id="timeout"
								type="number"
								bind:value={litellmForm.request_timeout_seconds}
								min="10"
								max="300"
							/>
							<p class="text-xs text-muted-foreground">Maximum time to wait for LLM responses</p>
						</div>
					</Card.Content>
				</Card.Root>
			</Tabs.Content>

			<!-- Notification Settings -->
			<Tabs.Content value="notification" class="mt-6">
				<Card.Root>
					<Card.Header>
						<Card.Title>Notification Settings</Card.Title>
						<Card.Description>Configure email and notification settings</Card.Description>
					</Card.Header>
					<Card.Content class="space-y-6">
						<!-- Slack -->
						<div class="space-y-4 rounded-lg border p-4">
							<h4 class="font-medium">Slack Notifications</h4>
							<div class="space-y-2">
								<Label for="slack_webhook">Webhook URL</Label>
								<div class="flex gap-2">
									<Input
										id="slack_webhook"
										type={visibleSecrets['slack_webhook'] ? 'text' : 'password'}
										bind:value={notificationForm.slack_webhook_url}
										placeholder="https://hooks.slack.com/services/..."
										class="flex-1"
									/>
									<Button
										variant="outline"
										size="icon"
										onclick={() => toggleSecretVisibility('slack_webhook')}
									>
										{#if visibleSecrets['slack_webhook']}
											<EyeOff class="h-4 w-4" />
										{:else}
											<Eye class="h-4 w-4" />
										{/if}
									</Button>
								</div>
								{#if isSecretMasked(notificationForm.slack_webhook_url)}
									<Badge variant="secondary" class="text-xs">Masked - enter new value to update</Badge>
								{/if}
							</div>
						</div>

						<!-- Email -->
						<div class="space-y-4 rounded-lg border p-4">
							<div class="flex items-center justify-between">
								<h4 class="font-medium">Email Notifications</h4>
								<Switch bind:checked={notificationForm.email_enabled} />
							</div>

							<div class="grid grid-cols-2 gap-4">
								<div class="space-y-2">
									<Label for="email_from_name">From Name</Label>
									<Input
										id="email_from_name"
										bind:value={notificationForm.email_from_name}
										placeholder="RAG Agent Platform"
									/>
								</div>

								<div class="space-y-2">
									<Label for="email_from_address">From Address</Label>
									<Input
										id="email_from_address"
										type="email"
										bind:value={notificationForm.email_from_address}
										placeholder="noreply@example.com"
									/>
								</div>
							</div>

							<div class="grid grid-cols-2 gap-4">
								<div class="space-y-2">
									<Label for="smtp_host">SMTP Host</Label>
									<Input
										id="smtp_host"
										bind:value={notificationForm.smtp_host}
										placeholder="smtp.example.com"
									/>
								</div>

								<div class="space-y-2">
									<Label for="smtp_port">SMTP Port</Label>
									<Input id="smtp_port" type="number" bind:value={notificationForm.smtp_port} />
								</div>
							</div>

							<div class="grid grid-cols-2 gap-4">
								<div class="space-y-2">
									<Label for="smtp_username">SMTP Username</Label>
									<Input
										id="smtp_username"
										bind:value={notificationForm.smtp_username}
										placeholder="username"
									/>
								</div>

								<div class="space-y-2">
									<Label for="smtp_password">SMTP Password</Label>
									<div class="flex gap-2">
										<Input
											id="smtp_password"
											type={visibleSecrets['smtp_password'] ? 'text' : 'password'}
											bind:value={notificationForm.smtp_password}
											placeholder="********"
											class="flex-1"
										/>
										<Button
											variant="outline"
											size="icon"
											onclick={() => toggleSecretVisibility('smtp_password')}
										>
											{#if visibleSecrets['smtp_password']}
												<EyeOff class="h-4 w-4" />
											{:else}
												<Eye class="h-4 w-4" />
											{/if}
										</Button>
									</div>
									{#if isSecretMasked(notificationForm.smtp_password)}
										<Badge variant="secondary" class="text-xs"
											>Masked - enter new value to update</Badge
										>
									{/if}
								</div>
							</div>

							<div class="flex items-center justify-between rounded-lg border p-3">
								<div class="space-y-0.5">
									<Label>Use TLS</Label>
									<p class="text-xs text-muted-foreground">Enable TLS encryption for SMTP</p>
								</div>
								<Switch bind:checked={notificationForm.smtp_use_tls} />
							</div>
						</div>
					</Card.Content>
				</Card.Root>
			</Tabs.Content>
		</Tabs.Root>
	{/if}
</div>
