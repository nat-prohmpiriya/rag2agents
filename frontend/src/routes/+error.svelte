<script lang="ts">
	import { page } from '$app/stores';
	import { Button } from '$lib/components/ui/button';

	let status = $derived($page.status);
	let message = $derived($page.error?.message || 'Something went wrong');

	const errorInfo: Record<number, { title: string; description: string; icon: string }> = {
		404: {
			title: 'Page Not Found',
			description: 'The page you are looking for does not exist or has been moved.',
			icon: '🔍'
		},
		500: {
			title: 'Server Error',
			description: 'Something went wrong on our end. Please try again later.',
			icon: '⚠️'
		},
		403: {
			title: 'Access Denied',
			description: 'You do not have permission to access this page.',
			icon: '🚫'
		},
		401: {
			title: 'Unauthorized',
			description: 'Please log in to access this page.',
			icon: '🔒'
		}
	};

	let info = $derived(
		errorInfo[status] || {
			title: 'Error',
			description: message,
			icon: '❌'
		}
	);
</script>

<svelte:head>
	<title>{status} - {info.title}</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center bg-background px-4">
	<div class="text-center max-w-md">
		<div class="text-6xl mb-6">{info.icon}</div>
		<h1 class="text-7xl font-bold text-primary mb-4">{status}</h1>
		<h2 class="text-2xl font-semibold text-foreground mb-2">{info.title}</h2>
		<p class="text-muted-foreground mb-8">{info.description}</p>

		<div class="flex flex-col sm:flex-row gap-3 justify-center">
			<Button href="/" variant="default">Go Home</Button>
			<Button onclick={() => history.back()} variant="outline">Go Back</Button>
		</div>
	</div>
</div>
