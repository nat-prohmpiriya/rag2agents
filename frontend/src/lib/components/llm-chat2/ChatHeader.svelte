<script lang="ts">
	import { ChevronDown, Share, MoreHorizontal, Trash2, Archive } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';

	interface Props {
		title?: string;
		onShare?: () => void;
		onDelete?: () => void;
		onArchive?: () => void;
		onRename?: () => void;
	}

	let { title = 'New conversation', onShare, onDelete, onArchive, onRename }: Props = $props();
</script>

<header
	class="flex items-center justify-between px-4 py-3 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
>
	<div class="flex items-center gap-1">
		<!-- Title with dropdown -->
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Button
						variant="ghost"
						class="gap-1 font-medium text-base h-auto py-1.5 px-2"
						{...props}
					>
						{title}
						<ChevronDown class="size-4 text-muted-foreground" />
					</Button>
				{/snippet}
			</DropdownMenu.Trigger>
			<DropdownMenu.Content align="start" class="w-48">
				<DropdownMenu.Item onclick={onRename}>Rename</DropdownMenu.Item>
				<DropdownMenu.Item onclick={onArchive}>
					<Archive class="mr-2 size-4" />
					Archive
				</DropdownMenu.Item>
				<DropdownMenu.Separator />
				<DropdownMenu.Item
					class="text-destructive focus:text-destructive"
					onclick={onDelete}
				>
					<Trash2 class="mr-2 size-4" />
					Delete
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</div>

	<div class="flex items-center gap-2">
		<!-- Share button -->
		<Button variant="outline" size="sm" class="gap-1.5" onclick={onShare}>
			<Share class="size-4" />
			Share
		</Button>
	</div>
</header>
