<script lang="ts">
	import { goto } from '$app/navigation';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import * as Card from '$lib/components/ui/card';
	import * as Alert from '$lib/components/ui/alert';
	import { auth } from '$lib/stores';
	import { ApiException } from '$lib/types';

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
			error = 'Passwords do not match';
			return;
		}

		if (password.length < 8) {
			error = 'Password must be at least 8 characters';
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
				error = 'An unexpected error occurred. Please try again.';
			}
		} finally {
			isLoading = false;
		}
	}
</script>

<svelte:head>
	<title>Register - RAG Agent Platform</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-background px-4">
	<Card.Root class="w-full max-w-md">
		<Card.Header class="space-y-1">
			<Card.Title class="text-2xl font-bold text-center">Create an account</Card.Title>
			<Card.Description class="text-center">
				Enter your details to get started
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
					<Label for="username">Username *</Label>
					<Input
						id="username"
						type="text"
						placeholder="johndoe"
						bind:value={username}
						required
						disabled={isLoading}
					/>
					{#if username && username.length < 3}
						<p class="text-xs text-destructive">Username must be at least 3 characters</p>
					{/if}
				</div>

				<div class="space-y-2">
					<Label for="email">Email *</Label>
					<Input
						id="email"
						type="email"
						placeholder="name@example.com"
						bind:value={email}
						required
						disabled={isLoading}
					/>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label for="firstName">First Name</Label>
						<Input
							id="firstName"
							type="text"
							placeholder="John"
							bind:value={firstName}
							disabled={isLoading}
						/>
					</div>
					<div class="space-y-2">
						<Label for="lastName">Last Name</Label>
						<Input
							id="lastName"
							type="text"
							placeholder="Doe"
							bind:value={lastName}
							disabled={isLoading}
						/>
					</div>
				</div>

				<div class="space-y-2">
					<Label for="password">Password *</Label>
					<Input
						id="password"
						type="password"
						placeholder="At least 8 characters"
						bind:value={password}
						required
						disabled={isLoading}
					/>
					{#if password && password.length < 8}
						<p class="text-xs text-destructive">Password must be at least 8 characters</p>
					{/if}
				</div>

				<div class="space-y-2">
					<Label for="confirmPassword">Confirm Password *</Label>
					<Input
						id="confirmPassword"
						type="password"
						placeholder="Confirm your password"
						bind:value={confirmPassword}
						required
						disabled={isLoading}
						class={!passwordsMatch ? 'border-destructive' : ''}
					/>
					{#if !passwordsMatch}
						<p class="text-xs text-destructive">Passwords do not match</p>
					{/if}
				</div>

				<Button type="submit" class="w-full" disabled={isLoading || !isValid}>
					{#if isLoading}
						<svg class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
						</svg>
						Creating account...
					{:else}
						Create account
					{/if}
				</Button>

				<p class="text-xs text-muted-foreground text-center">
					By creating an account, you agree to our
					<a href="/terms" class="text-primary hover:underline">Terms of Service</a>
					and
					<a href="/privacy" class="text-primary hover:underline">Privacy Policy</a>
				</p>
			</form>
		</Card.Content>
		<Card.Footer>
			<p class="text-center text-sm text-muted-foreground w-full">
				Already have an account?
				<a href="/login" class="text-primary hover:underline font-medium">
					Sign in
				</a>
			</p>
		</Card.Footer>
	</Card.Root>
</div>
