<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import * as Card from '$lib/components/ui/card';
	import * as Alert from '$lib/components/ui/alert';
	import { auth } from '$lib/stores';
	import { ApiException } from '$lib/types';
	import * as m from '$lib/paraglide/messages';

	let username = $state('');
	let email = $state('');
	let firstName = $state('');
	let lastName = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let isLoading = $state(false);
	let error = $state<string | null>(null);

	let passwordsMatch = $derived(password === confirmPassword || confirmPassword === '');
	let isValid = $derived(
		username.length >= 3 &&
		email.includes('@') &&
		password.length >= 8 &&
		password === confirmPassword
	);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = null;

		if (!passwordsMatch) {
			error = m.register_passwords_no_match();
			return;
		}

		if (password.length < 8) {
			error = m.register_password_min();
			return;
		}

		isLoading = true;

		try {
			await auth.register({
				username,
				email,
				password,
				first_name: firstName || undefined,
				last_name: lastName || undefined,
			});
			goto('/chat');
		} catch (err) {
			if (err instanceof ApiException) {
				error = err.message;
			} else {
				error = m.common_error_unexpected();
			}
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>{m.register_page_title()}</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-background px-4">
	<Card.Root class="w-full max-w-md">
		<Card.Header class="space-y-1">
			<Card.Title class="text-2xl font-bold text-center">{m.register_title()}</Card.Title>
			<Card.Description class="text-center">
				{m.register_description()}
			</Card.Description>
		</Card.Header>
		<Card.Content>
			<form onsubmit={handleSubmit} class="space-y-4">
				{#if error}
					<Alert.Root variant="destructive">
						<Alert.Description>{error}</Alert.Description>
					</Alert.Root>
				{/if}

				<div class="space-y-2">
					<Label for="username">{m.register_username()} *</Label>
					<Input
						id="username"
						type="text"
						placeholder={m.register_username_placeholder()}
						bind:value={username}
						required
						disabled={isLoading}
					/>
					{#if username && username.length < 3}
						<p class="text-xs text-destructive">{m.register_username_min()}</p>
					{/if}
				</div>

				<div class="space-y-2">
					<Label for="email">{m.auth_email()} *</Label>
					<Input
						id="email"
						type="email"
						placeholder={m.auth_email_placeholder()}
						bind:value={email}
						required
						disabled={isLoading}
					/>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label for="firstName">{m.register_first_name()}</Label>
						<Input
							id="firstName"
							type="text"
							placeholder={m.register_first_name_placeholder()}
							bind:value={firstName}
							disabled={isLoading}
						/>
					</div>
					<div class="space-y-2">
						<Label for="lastName">{m.register_last_name()}</Label>
						<Input
							id="lastName"
							type="text"
							placeholder={m.register_last_name_placeholder()}
							bind:value={lastName}
							disabled={isLoading}
						/>
					</div>
				</div>

				<div class="space-y-2">
					<Label for="password">{m.auth_password()} *</Label>
					<Input
						id="password"
						type="password"
						placeholder={m.register_password_placeholder()}
						bind:value={password}
						required
						disabled={isLoading}
					/>
					{#if password && password.length < 8}
						<p class="text-xs text-destructive">{m.register_password_min()}</p>
					{/if}
				</div>

				<div class="space-y-2">
					<Label for="confirmPassword">{m.register_confirm_password()} *</Label>
					<Input
						id="confirmPassword"
						type="password"
						placeholder={m.register_confirm_password_placeholder()}
						bind:value={confirmPassword}
						required
						disabled={isLoading}
						class={!passwordsMatch ? 'border-destructive' : ''}
					/>
					{#if !passwordsMatch}
						<p class="text-xs text-destructive">{m.register_passwords_no_match()}</p>
					{/if}
				</div>

				<Button type="submit" class="w-full" disabled={isLoading || !isValid}>
					{#if isLoading}
						<svg class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
						</svg>
						{m.register_creating_account()}
					{:else}
						{m.register_create_account()}
					{/if}
				</Button>

				<p class="text-xs text-muted-foreground text-center">
					{m.register_agree_terms()}
					<a href="/terms" class="text-primary hover:underline">{m.register_terms_of_service()}</a>
					{m.register_and()}
					<a href="/privacy" class="text-primary hover:underline">{m.register_privacy_policy()}</a>
				</p>
			</form>
		</Card.Content>
		<Card.Footer>
			<p class="text-center text-sm text-muted-foreground w-full">
				{m.register_have_account()}
				<a href="/login" class="text-primary hover:underline font-medium">
					{m.auth_sign_in()}
				</a>
			</p>
		</Card.Footer>
	</Card.Root>
</div>
