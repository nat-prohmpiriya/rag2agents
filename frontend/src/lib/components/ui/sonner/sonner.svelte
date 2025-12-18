<script lang="ts">
	import { Toaster as Sonner, type ToasterProps as SonnerProps } from "svelte-sonner";
	import { mode } from "mode-watcher";

	let { ...restProps }: SonnerProps = $props();
</script>

<Sonner
	theme={mode.current}
	class="toaster group"
	style="
		--normal-bg: var(--color-popover);
		--normal-text: var(--color-popover-foreground);
		--normal-border: var(--color-border);
		--error-bg: var(--color-destructive);
		--error-text: white;
		--error-border: var(--color-destructive);
		--success-bg: #10b981;
		--success-text: white;
		--success-border: #10b981;
	"
	{...restProps}
/>
