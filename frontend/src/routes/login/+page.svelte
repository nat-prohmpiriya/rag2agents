<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Eye, EyeOff } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import * as Card from '$lib/components/ui/card';
	import * as Alert from '$lib/components/ui/alert';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { auth } from '$lib/stores';
	import { ApiException } from '$lib/types';

	const REMEMBER_EMAIL_KEY = 'rag_remember_email';

	let email = $state('');
	let password = $state('');
	let isLoading = $state(false);
	let error = $state<string | null>(null);
	let showPassword = $state(false);
	let rememberEmail = $state(false);

	onMount(() => {
		// Load remembered email from localStorage
		const savedEmail = localStorage.getItem(REMEMBER_EMAIL_KEY);
		if (savedEmail) {
			email = savedEmail;
			rememberEmail = true;
		}
	});

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = null;
		isLoading = true;

		try {
			// Save or clear remembered email
			if (rememberEmail) {
				localStorage.setItem(REMEMBER_EMAIL_KEY, email);
			} else {
				localStorage.removeItem(REMEMBER_EMAIL_KEY);
			}

			await auth.login({ email, password });
			goto('/dashboard');
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

	function togglePasswordVisibility() {
		showPassword = !showPassword;
	}
</script>

<svelte:head>
	<title>Login - RAG Agent Platform</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-background px-4">
	<Card.Root class="w-full max-w-md">
		<Card.Header class="space-y-1">
			<Card.Title class="text-2xl font-bold text-center">Welcome back</Card.Title>
			<Card.Description class="text-center">
				Enter your credentials to access your account
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
					<Label for="email">Email</Label>
					<Input
						id="email"
						type="email"
						placeholder="name@example.com"
						bind:value={email}
						required
						disabled={isLoading}
					/>
				</div>

				<div class="space-y-2">
					<div class="flex items-center justify-between">
						<Label for="password">Password</Label>
						<a href="/forgot-password" class="text-sm text-primary hover:underline">
							Forgot password?
						</a>
					</div>
					<div class="relative">
						<Input
							id="password"
							type={showPassword ? 'text' : 'password'}
							placeholder="Enter your password"
							bind:value={password}
							required
							disabled={isLoading}
							class="pr-10"
						/>
						<button
							type="button"
							onclick={togglePasswordVisibility}
							class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
							tabindex={-1}
						>
							{#if showPassword}
								<EyeOff class="size-4" />
							{:else}
								<Eye class="size-4" />
							{/if}
						</button>
					</div>
				</div>

				<div class="flex items-center space-x-2">
					<Checkbox
						id="remember"
						bind:checked={rememberEmail}
						disabled={isLoading}
					/>
					<Label for="remember" class="text-sm font-normal cursor-pointer">
						Remember my email
					</Label>
				</div>

				<Button type="submit" class="w-full" disabled={isLoading}>
					{#if isLoading}
						<svg class="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24">
							<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
							<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
						</svg>
						Signing in...
					{:else}
						Sign in
					{/if}
				</Button>
			</form>
		</Card.Content>
		<Card.Footer class="flex flex-col space-y-4">
			<div class="relative w-full">
				<div class="absolute inset-0 flex items-center">
					<span class="w-full border-t"></span>
				</div>
				<div class="relative flex justify-center text-xs uppercase">
					<span class="bg-background px-2 text-muted-foreground">Or</span>
				</div>
			</div>
			<p class="text-center text-sm text-muted-foreground">
				Don't have an account?
				<a href="/register" class="text-primary hover:underline font-medium">
					Sign up
				</a>
			</p>
		</Card.Footer>
	</Card.Root>
</div>
