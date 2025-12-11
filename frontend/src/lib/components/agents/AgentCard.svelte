<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { MoreVertical, Pencil, Trash2 } from 'lucide-svelte';
	import type { AgentInfo } from '$lib/api';

	interface Props {
		agent: AgentInfo;
		selected?: boolean;
		onclick?: () => void;
		onEdit?: () => void;
		onDelete?: () => void;
	}

	let { agent, selected = false, onclick, onEdit, onDelete }: Props = $props();

	let isUserAgent = $derived(agent.source === 'user');

	function getAgentIcon(icon?: string): string {
		if (!icon) return '🤖';
		const iconMap: Record<string, string> = {
			search: '🔍',
			calculator: '🔢',
			code: '💻',
			write: '✍️',
			chart: '📊',
			brain: '🧠',
			robot: '🤖',
			sparkles: '✨',
		};
		return iconMap[icon] || '🤖';
	}
</script>

<button
	type="button"
	class="w-full h-full text-left cursor-pointer group"
	onclick={onclick}
>
	<Card.Root
		class="h-full flex flex-col transition-all hover:shadow-md {selected
			? 'ring-2 ring-primary border-primary'
			: 'hover:border-muted-foreground/50'}"
	>
		<Card.Header class="pb-3">
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3 flex-1">
					<span class="text-2xl">{getAgentIcon(agent.icon)}</span>
					<Card.Title class="text-base">{agent.name}</Card.Title>
				</div>
				<div class="flex items-center gap-1">
					{#if !isUserAgent}
						<Badge variant="outline" class="text-xs">System</Badge>
					{/if}
					{#if isUserAgent && (onEdit || onDelete)}
						<DropdownMenu.Root>
							<DropdownMenu.Trigger>
								{#snippet child({ props })}
									<Button
										{...props}
										variant="ghost"
										size="sm"
										class="size-8 p-0 opacity-0 group-hover:opacity-100"
										onclick={(e: MouseEvent) => e.stopPropagation()}
									>
										<MoreVertical class="size-4" />
									</Button>
								{/snippet}
							</DropdownMenu.Trigger>
							<DropdownMenu.Content align="end">
								{#if onEdit}
									<DropdownMenu.Item onclick={(e: Event) => { e.stopPropagation(); onEdit?.(); }}>
										<Pencil class="mr-2 size-4" />
										Edit
									</DropdownMenu.Item>
								{/if}
								{#if onDelete}
									<DropdownMenu.Separator />
									<DropdownMenu.Item
										class="text-destructive"
										onclick={(e: Event) => { e.stopPropagation(); onDelete?.(); }}
									>
										<Trash2 class="mr-2 size-4" />
										Delete
									</DropdownMenu.Item>
								{/if}
							</DropdownMenu.Content>
						</DropdownMenu.Root>
					{/if}
				</div>
			</div>
		</Card.Header>
		<Card.Content class="pt-0 flex-1 flex flex-col">
			<p class="text-sm text-muted-foreground mb-3 line-clamp-2 min-h-[2.5rem]">
				{agent.description || ''}
			</p>
			<div class="flex flex-wrap gap-1.5 mt-auto">
				{#if agent.tools && agent.tools.length > 0}
					{#each agent.tools as tool}
						<Badge variant="secondary" class="text-xs">
							{tool}
						</Badge>
					{/each}
				{/if}
			</div>
		</Card.Content>
	</Card.Root>
</button>
