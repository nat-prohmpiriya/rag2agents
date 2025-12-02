<script lang="ts">
	import { ScrollArea } from '$lib/components/ui/scroll-area';
	import ChatMessage from './ChatMessage.svelte';
	import ChatInput from './ChatInput.svelte';

	interface Message {
		id: string;
		role: 'user' | 'assistant';
		content: string;
	}

	let { messages = [], isStreaming = false, streamingContent = '', onSend } = $props<{
		messages?: Message[];
		isStreaming?: boolean;
		streamingContent?: string;
		onSend: (message: string) => void;
	}>();

	let scrollAreaRef = $state<HTMLDivElement | null>(null);

	// Auto-scroll to bottom when new messages arrive
	$effect(() => {
		if (scrollAreaRef && (messages.length > 0 || streamingContent)) {
			// Small delay to ensure DOM is updated
			setTimeout(() => {
				scrollAreaRef?.scrollTo({
					top: scrollAreaRef.scrollHeight,
					behavior: 'smooth',
				});
			}, 50);
		}
	});
</script>

<div class="flex flex-col h-full">
	<!-- Messages area -->
	<div class="flex-1 overflow-hidden">
		<div bind:this={scrollAreaRef} class="h-full overflow-y-auto p-4">
			{#if messages.length === 0 && !isStreaming}
				<!-- Empty state -->
				<div class="flex flex-col items-center justify-center h-full text-center">
					<svg
						class="h-12 w-12 text-muted-foreground/50 mb-4"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
					>
						<path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
					</svg>
					<h3 class="font-semibold text-lg mb-2">Start a conversation</h3>
					<p class="text-muted-foreground text-sm max-w-sm">
						Ask me anything! I can help you with questions, writing, coding, and more.
					</p>
				</div>
			{:else}
				<div class="space-y-4">
					{#each messages as msg (msg.id)}
						<ChatMessage
							message={msg.content}
							isUser={msg.role === 'user'}
						/>
					{/each}

					{#if isStreaming}
						<ChatMessage
							message={streamingContent}
							isUser={false}
							isStreaming={true}
						/>
					{/if}
				</div>
			{/if}
		</div>
	</div>

	<!-- Input area -->
	<div class="border-t p-4 bg-background">
		<ChatInput
			{onSend}
			disabled={isStreaming}
			placeholder={isStreaming ? 'Waiting for response...' : 'Type your message...'}
		/>
	</div>
</div>
