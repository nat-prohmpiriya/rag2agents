<script lang="ts">
	import { Button } from '$lib/components/ui/button';

	let { onSend, disabled = false, placeholder = 'Type your message...' } = $props<{
		onSend: (message: string) => void;
		disabled?: boolean;
		placeholder?: string;
	}>();

	let message = $state('');
	let textareaRef = $state<HTMLTextAreaElement | null>(null);

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (message.trim() && !disabled) {
			onSend(message.trim());
			message = '';
			// Reset textarea height
			if (textareaRef) {
				textareaRef.style.height = 'auto';
			}
		}
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit(e);
		}
	}

	function handleInput() {
		if (textareaRef) {
			// Auto-resize textarea
			textareaRef.style.height = 'auto';
			textareaRef.style.height = Math.min(textareaRef.scrollHeight, 200) + 'px';
		}
	}
</script>

<form onsubmit={handleSubmit} class="flex gap-2 items-end">
	<div class="flex-1 relative">
		<textarea
			bind:this={textareaRef}
			bind:value={message}
			onkeydown={handleKeyDown}
			oninput={handleInput}
			{placeholder}
			{disabled}
			rows="1"
			class="w-full resize-none rounded-lg border border-input bg-background px-4 py-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 min-h-[48px] max-h-[200px]"
		></textarea>
	</div>
	<Button
		type="submit"
		size="icon"
		class="h-12 w-12 shrink-0"
		disabled={disabled || !message.trim()}
	>
		<svg
			class="h-5 w-5"
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
		>
			<path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
		</svg>
		<span class="sr-only">Send message</span>
	</Button>
</form>
