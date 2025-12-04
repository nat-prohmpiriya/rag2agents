<script lang="ts">
	import { onMount } from 'svelte';
	import { Bell, Save, Loader2, CreditCard, FileText, Settings, User, Moon } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Switch } from '$lib/components/ui/switch';
	import { Label } from '$lib/components/ui/label';
	import { Input } from '$lib/components/ui/input';
	import * as Card from '$lib/components/ui/card';
	import { Separator } from '$lib/components/ui/separator';
	import { notificationStore } from '$lib/stores';
	import type { CategorySettings, NotificationPreferenceUpdate } from '$lib/api';

	let loading = $state(true);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let successMessage = $state<string | null>(null);

	// Form state
	let emailEnabled = $state(true);
	let inAppEnabled = $state(true);
	let quietHoursEnabled = $state(false);
	let quietHoursStart = $state('22:00');
	let quietHoursEnd = $state('08:00');
	let categorySettings = $state<CategorySettings>({
		billing: { email: true, in_app: true },
		document: { email: true, in_app: true },
		system: { email: true, in_app: true },
		account: { email: true, in_app: true }
	});

	// Category info
	const categories = [
		{
			key: 'billing' as const,
			label: 'Billing & Payments',
			description: 'Payment confirmations, subscription updates, quota warnings',
			icon: CreditCard
		},
		{
			key: 'document' as const,
			label: 'Documents',
			description: 'Document processing status, upload completions',
			icon: FileText
		},
		{
			key: 'system' as const,
			label: 'System',
			description: 'Maintenance notices, feature updates, announcements',
			icon: Settings
		},
		{
			key: 'account' as const,
			label: 'Account',
			description: 'Security alerts, password changes, profile updates',
			icon: User
		}
	];

	onMount(async () => {
		await loadPreferences();
	});

	async function loadPreferences() {
		loading = true;
		error = null;

		try {
			await notificationStore.fetchPreferences();
			const prefs = notificationStore.preferences;

			if (prefs) {
				emailEnabled = prefs.email_enabled;
				inAppEnabled = prefs.in_app_enabled;
				categorySettings = { ...prefs.category_settings };
				quietHoursEnabled = !!(prefs.quiet_hours_start && prefs.quiet_hours_end);
				if (prefs.quiet_hours_start) quietHoursStart = prefs.quiet_hours_start;
				if (prefs.quiet_hours_end) quietHoursEnd = prefs.quiet_hours_end;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load preferences';
		} finally {
			loading = false;
		}
	}

	async function handleSave() {
		saving = true;
		error = null;
		successMessage = null;

		try {
			const update: NotificationPreferenceUpdate = {
				email_enabled: emailEnabled,
				in_app_enabled: inAppEnabled,
				category_settings: categorySettings,
				quiet_hours_start: quietHoursEnabled ? quietHoursStart : null,
				quiet_hours_end: quietHoursEnabled ? quietHoursEnd : null
			};

			const success = await notificationStore.updatePreferences(update);

			if (success) {
				successMessage = 'Preferences saved successfully';
				setTimeout(() => (successMessage = null), 3000);
			} else {
				error = 'Failed to save preferences';
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save preferences';
		} finally {
			saving = false;
		}
	}

	function toggleCategoryEmail(key: keyof CategorySettings) {
		categorySettings[key].email = !categorySettings[key].email;
	}

	function toggleCategoryInApp(key: keyof CategorySettings) {
		categorySettings[key].in_app = !categorySettings[key].in_app;
	}
</script>

<div class="space-y-6">
	<!-- Header with Save button -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-3">
			<Bell class="size-6 text-muted-foreground" />
			<div>
				<h2 class="text-lg font-semibold">Notification Preferences</h2>
				<p class="text-sm text-muted-foreground">Manage how and when you receive notifications</p>
			</div>
		</div>
		<Button onclick={handleSave} disabled={saving || loading}>
			{#if saving}
				<Loader2 class="size-4 animate-spin mr-2" />
			{:else}
				<Save class="size-4 mr-2" />
			{/if}
			Save Changes
		</Button>
	</div>

	<!-- Messages -->
	{#if error}
		<div class="rounded-md bg-destructive/10 p-4 text-destructive text-sm">
			{error}
		</div>
	{/if}

	{#if successMessage}
		<div class="rounded-md bg-green-500/10 p-4 text-green-600 dark:text-green-400 text-sm">
			{successMessage}
		</div>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<div class="size-8 animate-spin rounded-full border-4 border-muted border-t-primary"></div>
		</div>
	{:else}
		<!-- Global Settings -->
		<Card.Root>
			<Card.Header>
				<Card.Title>Notification Channels</Card.Title>
				<Card.Description>Choose how you want to receive notifications</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-4">
				<div class="flex items-center justify-between rounded-lg border p-4">
					<div class="space-y-0.5">
						<Label class="text-base">Email Notifications</Label>
						<p class="text-sm text-muted-foreground">
							Receive notifications via email
						</p>
					</div>
					<Switch bind:checked={emailEnabled} />
				</div>

				<div class="flex items-center justify-between rounded-lg border p-4">
					<div class="space-y-0.5">
						<Label class="text-base">In-App Notifications</Label>
						<p class="text-sm text-muted-foreground">
							Show notifications in the app
						</p>
					</div>
					<Switch bind:checked={inAppEnabled} />
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Category Settings -->
		<Card.Root>
			<Card.Header>
				<Card.Title>Category Settings</Card.Title>
				<Card.Description>Fine-tune notifications for each category</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="space-y-4">
					{#each categories as category}
						{@const Icon = category.icon}
						<div class="rounded-lg border p-4">
							<div class="flex items-start gap-3 mb-3">
								<div class="rounded-lg bg-muted p-2">
									<Icon class="size-5 text-muted-foreground" />
								</div>
								<div class="flex-1">
									<Label class="text-base">{category.label}</Label>
									<p class="text-sm text-muted-foreground">{category.description}</p>
								</div>
							</div>
							<Separator class="my-3" />
							<div class="flex items-center gap-6 pl-11">
								<label class="flex items-center gap-2 cursor-pointer">
									<Switch
										checked={categorySettings[category.key].email}
										onCheckedChange={() => toggleCategoryEmail(category.key)}
										disabled={!emailEnabled}
									/>
									<span class="text-sm {!emailEnabled ? 'text-muted-foreground' : ''}">Email</span>
								</label>
								<label class="flex items-center gap-2 cursor-pointer">
									<Switch
										checked={categorySettings[category.key].in_app}
										onCheckedChange={() => toggleCategoryInApp(category.key)}
										disabled={!inAppEnabled}
									/>
									<span class="text-sm {!inAppEnabled ? 'text-muted-foreground' : ''}">In-App</span>
								</label>
							</div>
						</div>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Quiet Hours -->
		<Card.Root>
			<Card.Header>
				<Card.Title class="flex items-center gap-2">
					<Moon class="size-5" />
					Quiet Hours
				</Card.Title>
				<Card.Description>Pause non-critical notifications during specific hours</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-4">
				<div class="flex items-center justify-between rounded-lg border p-4">
					<div class="space-y-0.5">
						<Label class="text-base">Enable Quiet Hours</Label>
						<p class="text-sm text-muted-foreground">
							Only critical notifications will be sent during quiet hours
						</p>
					</div>
					<Switch bind:checked={quietHoursEnabled} />
				</div>

				{#if quietHoursEnabled}
					<div class="grid grid-cols-2 gap-4 pl-4">
						<div class="space-y-2">
							<Label for="quiet-start">Start Time</Label>
							<Input id="quiet-start" type="time" bind:value={quietHoursStart} />
						</div>
						<div class="space-y-2">
							<Label for="quiet-end">End Time</Label>
							<Input id="quiet-end" type="time" bind:value={quietHoursEnd} />
						</div>
					</div>
					<p class="text-xs text-muted-foreground pl-4">
						Quiet hours: {quietHoursStart} - {quietHoursEnd}
					</p>
				{/if}
			</Card.Content>
		</Card.Root>

		<!-- Save Button (mobile) -->
		<div class="md:hidden">
			<Button onclick={handleSave} disabled={saving || loading} class="w-full">
				{#if saving}
					<Loader2 class="size-4 animate-spin mr-2" />
				{:else}
					<Save class="size-4 mr-2" />
				{/if}
				Save Changes
			</Button>
		</div>
	{/if}
</div>
