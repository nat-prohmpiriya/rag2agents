<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Textarea } from '$lib/components/ui/textarea';
	import { Label } from '$lib/components/ui/label';
	import type { Project, ProjectCreate, ProjectUpdate } from '$lib/api';

	let {
		open = $bindable(false),
		project = null,
		onSave
	} = $props<{
		open: boolean;
		project: Project | null;
		onSave: (data: ProjectCreate | ProjectUpdate) => Promise<void>;
	}>();

	let name = $state('');
	let description = $state('');
	let saving = $state(false);
	let error = $state<string | null>(null);

	// Derived states
	let isEdit = $derived(project !== null);
	let title = $derived(isEdit ? 'Edit Project' : 'Create Project');
	let submitLabel = $derived(isEdit ? 'Save Changes' : 'Create');
	let isValid = $derived(name.trim().length > 0 && name.trim().length <= 255);

	// Reset form when dialog opens/closes or project changes
	$effect(() => {
		if (open) {
			if (project) {
				name = project.name;
				description = project.description || '';
			} else {
				name = '';
				description = '';
			}
			error = null;
		}
	});

	async function handleSubmit() {
		if (!isValid || saving) return;

		saving = true;
		error = null;

		try {
			const data: ProjectCreate | ProjectUpdate = {
				name: name.trim(),
				description: description.trim() || null
			};

			await onSave(data);
			open = false;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save project';
		} finally {
			saving = false;
		}
	}

	function handleClose() {
		if (!saving) {
			open = false;
		}
	}
</script>

<Dialog.Root bind:open onOpenChange={(isOpen) => !isOpen && handleClose()}>
	<Dialog.Portal>
		<Dialog.Overlay />
		<Dialog.Content class="sm:max-w-md">
			<Dialog.Header>
				<Dialog.Title>{title}</Dialog.Title>
				<Dialog.Description>
					{isEdit ? 'Update the project details below.' : 'Enter the details for your new project.'}
				</Dialog.Description>
			</Dialog.Header>

			<form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }} class="space-y-4">
				<div class="space-y-2">
					<Label for="project-name">Name *</Label>
					<Input
						id="project-name"
						bind:value={name}
						placeholder="My Project"
						maxlength={255}
						disabled={saving}
						class={name.trim().length === 0 && name.length > 0 ? 'border-destructive' : ''}
					/>
					{#if name.length > 0 && name.trim().length === 0}
						<p class="text-xs text-destructive">Name cannot be empty or whitespace only</p>
					{/if}
				</div>

				<div class="space-y-2">
					<Label for="project-description">Description</Label>
					<Textarea
						id="project-description"
						bind:value={description}
						placeholder="Optional description..."
						rows={3}
						disabled={saving}
					/>
				</div>

				{#if error}
					<p class="text-sm text-destructive">{error}</p>
				{/if}

				<Dialog.Footer>
					<Button type="button" variant="outline" onclick={handleClose} disabled={saving}>
						Cancel
					</Button>
					<Button type="submit" disabled={!isValid || saving}>
						{#if saving}
							Saving...
						{:else}
							{submitLabel}
						{/if}
					</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
