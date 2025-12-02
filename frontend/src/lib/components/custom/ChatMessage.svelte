<script lang="ts">
	import * as Avatar from '$lib/components/ui/avatar';
	import { parseMarkdown } from '$lib/utils';

	let { message, isUser = false, isStreaming = false } = $props<{
		message: string;
		isUser?: boolean;
		isStreaming?: boolean;
	}>();

	let htmlContent = $derived(isUser ? message : parseMarkdown(message));
</script>

<div class="flex gap-3 {isUser ? 'flex-row-reverse' : ''}">
	<!-- Avatar -->
	<Avatar.Root class="h-8 w-8 shrink-0">
		<Avatar.Fallback class={isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}>
			{isUser ? 'U' : 'AI'}
		</Avatar.Fallback>
	</Avatar.Root>

	<!-- Message bubble -->
	<div
		class="max-w-[80%] rounded-lg px-4 py-2 {isUser
			? 'bg-primary text-primary-foreground'
			: 'bg-muted'}"
	>
		{#if isStreaming && !message}
			<span class="inline-flex gap-1">
				<span class="animate-bounce">.</span>
				<span class="animate-bounce" style="animation-delay: 0.1s">.</span>
				<span class="animate-bounce" style="animation-delay: 0.2s">.</span>
			</span>
		{:else if isUser}
			<p class="whitespace-pre-wrap m-0 text-sm">{message}</p>
		{:else}
			<!-- Markdown rendered content -->
			<div class="prose prose-sm dark:prose-invert max-w-none prose-p:my-2 prose-pre:my-2 prose-pre:bg-slate-900 prose-pre:text-slate-50 prose-code:before:content-none prose-code:after:content-none">
				{@html htmlContent}
			</div>
		{/if}
	</div>
</div>
