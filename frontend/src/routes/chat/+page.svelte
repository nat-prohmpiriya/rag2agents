<script lang="ts">
	import { goto } from '$app/navigation';
	import { AppLayout, ChatWindow } from '$lib/components/custom';
	import { auth } from '$lib/stores';
	import { chatApi } from '$lib/api';
	import { getUserDisplayName, ApiException } from '$lib/types';
	import { toast } from 'svelte-sonner';

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
	}

	// Mock projects for now
	const mockProjects = [
		{ id: '1', name: 'Research Project' },
		{ id: '2', name: 'HR Documents' },
	];

	let currentProject = $state(mockProjects[0]);
	let messages = $state<Message[]>([]);
	let isStreaming = $state(false);
	let streamingContent = $state('');

	// Redirect if not authenticated
	$effect(() => {
		if (!auth.isLoading && !auth.isAuthenticated) {
			goto('/login');
		}
	});

	function handleLogout() {
		auth.logout();
		goto('/login');
	}

	function handleNewProject() {
		console.log('New project');
	}

	function handleProjectSelect(projectId: string) {
		const project = mockProjects.find((p) => p.id === projectId);
		if (project) {
			currentProject = project;
		}
	}

	async function handleSendMessage(content: string) {
		// Add user message
		const userMessage: Message = {
			id: crypto.randomUUID(),
			role: 'user',
			content,
		};
		messages = [...messages, userMessage];

		// Start streaming
		isStreaming = true;
		streamingContent = '';

		try {
			await chatApi.stream(
				{ message: content },
				// onChunk
				(chunk) => {
					streamingContent += chunk;
				},
				// onDone
				() => {
					// Add assistant message
					const assistantMessage: Message = {
						id: crypto.randomUUID(),
						role: 'assistant',
						content: streamingContent,
					};
					messages = [...messages, assistantMessage];
					streamingContent = '';
					isStreaming = false;
				},
				// onError
				(error) => {
					toast.error('Chat Error', {
						description: error,
					});
					isStreaming = false;
					streamingContent = '';
				}
			);
		} catch (err) {
			isStreaming = false;
			streamingContent = '';
			if (err instanceof ApiException) {
				if (err.status === 401) {
					toast.error('Session expired', {
						description: 'Please login again.',
					});
					goto('/login');
				} else {
					toast.error('Chat Error', {
						description: err.message,
					});
				}
			} else {
				toast.error('Chat Error', {
					description: 'An unexpected error occurred.',
				});
			}
		}
	}
</script>

<svelte:head>
	<title>Chat - RAG Agent Platform</title>
</svelte:head>

{#if auth.isLoading}
	<div class="min-h-screen flex items-center justify-center bg-background">
		<div class="flex flex-col items-center gap-4">
			<svg class="h-8 w-8 animate-spin text-primary" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
			</svg>
			<p class="text-muted-foreground">Loading...</p>
		</div>
	</div>
{:else if auth.isAuthenticated}
	<AppLayout
		user={auth.user ? { name: getUserDisplayName(auth.user), email: auth.user.email } : null}
		{currentProject}
		projects={mockProjects}
		onLogout={handleLogout}
		onNewProject={handleNewProject}
		onProjectSelect={handleProjectSelect}
	>
		<div class="h-[calc(100vh-8rem)] flex flex-col">
			<div class="mb-4">
				<h1 class="text-2xl font-bold">Chat</h1>
				<p class="text-muted-foreground">Ask questions about your documents</p>
			</div>
			<div class="flex-1 border rounded-lg overflow-hidden bg-background">
				<ChatWindow
					{messages}
					{isStreaming}
					{streamingContent}
					onSend={handleSendMessage}
				/>
			</div>
		</div>
	</AppLayout>
{/if}
