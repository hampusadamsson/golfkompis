<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Tabs, TabsList, TabsTrigger } from '$lib/components/ui/tabs';
	import * as AlertDialog from '$lib/components/ui/alert-dialog';
	import { Label } from '$lib/components/ui/label';
	import RefreshCwIcon from '@lucide/svelte/icons/refresh-cw';

	import { createApiClient, getErrorMessage } from '$lib/api';
	import type { QueueEntry, QueueStatus, Course } from '$lib/api';
	import QueueEntryCard from './QueueEntryCard.svelte';
	import CourseMultiSelect from './CourseMultiSelect.svelte';

	interface Props {
		apiBaseUrl?: string;
	}

	let { apiBaseUrl = '' }: Props = $props();

	let activeTab = $state<QueueStatus>('active');
	let entries = $state<QueueEntry[]>([]);
	let courses = $state<Course[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let editingEntry = $state<QueueEntry | null>(null);
	let pendingCancelEntry = $state<QueueEntry | null>(null);
	let actionAlert = $state<{ kind: 'success' | 'error'; msg: string } | null>(null);

	// Edit form state
	let editCourseIds = $state<string[]>([]);
	let editStart = $state('');
	let editStop = $state('');
	let editSpots = $state(1);
	let editSaving = $state(false);
	let editError = $state<string | null>(null);

	const courseMap = $derived(new Map(courses.map((c) => [c.CourseID, c])));

	let cancelDialogOpen = $state(false);

	$effect(() => {
		cancelDialogOpen = pendingCancelEntry !== null;
	});

	export function refresh() {
		void load();
	}

	async function load() {
		loading = true;
		error = null;
		try {
			const api = createApiClient({ baseUrl: apiBaseUrl });
			const [entriesResult, coursesResult] = await Promise.all([
				api.listQueue({ status: activeTab }),
				api.listCourses()
			]);
			entries = entriesResult;
			courses = coursesResult;
		} catch (e) {
			error = getErrorMessage(e, { default: 'Kunde inte hämta köade sökningar.' });
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		// Fires on mount and whenever activeTab changes
		activeTab;
		void load();
	});

	$effect(() => {
		if (!actionAlert) return;
		const t = setTimeout(() => (actionAlert = null), 5000);
		return () => clearTimeout(t);
	});

	function openEdit(entry: QueueEntry) {
		editingEntry = entry;
		editCourseIds = [...entry.course_ids];
		editStart = entry.start_time?.slice(0, 5) ?? '';
		editStop = entry.stop_time?.slice(0, 5) ?? '';
		editSpots = entry.min_spots;
		editError = null;
	}

	async function saveEdit() {
		if (!editingEntry) return;
		editSaving = true;
		editError = null;
		try {
			const api = createApiClient({ baseUrl: apiBaseUrl });
			await api.updateQueueEntry(editingEntry.id, {
				course_ids: editCourseIds.length > 0 ? editCourseIds : undefined,
				start_time: editStart || null,
				stop_time: editStop || null,
				min_spots: editSpots
			});
			editingEntry = null;
			actionAlert = { kind: 'success', msg: 'Sökningen uppdaterades.' };
			void load();
		} catch (e) {
			editError = getErrorMessage(e, {
				conflict: 'Sökningen är inte längre aktiv.',
				not_found: 'En eller flera banor kunde inte hittas.',
				default: 'Kunde inte spara.'
			});
		} finally {
			editSaving = false;
		}
	}

	async function confirmCancel() {
		if (!pendingCancelEntry) return;
		const id = pendingCancelEntry.id;
		pendingCancelEntry = null;
		try {
			const api = createApiClient({ baseUrl: apiBaseUrl });
			await api.cancelQueueEntry(id);
			actionAlert = { kind: 'success', msg: 'Sökning avbruten.' };
			void load();
		} catch (e) {
			actionAlert = {
				kind: 'error',
				msg: getErrorMessage(e, { default: 'Kunde inte avbryta sökning.' })
			};
		}
	}

	function formatTargetDate(dateStr: string): string {
		return new Date(dateStr + 'T12:00:00').toLocaleDateString('sv-SE', {
			weekday: 'short',
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<section class="rounded-xl border p-4">
	<!-- Header -->
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-xl font-semibold">Mina köade sökningar</h2>
		<Button variant="ghost" size="sm" onclick={() => void load()} disabled={loading}>
			<RefreshCwIcon class="h-4 w-4 {loading ? 'animate-spin' : ''}" />
		</Button>
	</div>

	<!-- Tabs -->
	<Tabs bind:value={activeTab}>
		<TabsList class="mb-4">
			<TabsTrigger value="active">Aktiva</TabsTrigger>
			<TabsTrigger value="matched">Matchade</TabsTrigger>
			<TabsTrigger value="expired">Utgångna</TabsTrigger>
			<TabsTrigger value="cancelled">Avbrutna</TabsTrigger>
		</TabsList>
	</Tabs>

	<!-- Action alert -->
	{#if actionAlert}
		<div
			class="mb-4 rounded-md border px-4 py-3 text-sm {actionAlert.kind === 'success'
				? 'border-green-200 bg-green-50 text-green-800'
				: 'border-destructive/30 bg-destructive/10 text-destructive'}"
			role="alert"
		>
			{actionAlert.msg}
		</div>
	{/if}

	<!-- Error -->
	{#if error}
		<div class="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive" role="alert">
			{error}
		</div>
	{/if}

	<!-- Loading skeletons -->
	{#if loading}
		<div class="space-y-3">
			{#each [0, 1, 2] as n (n)}
				<div class="h-20 w-full animate-pulse rounded-xl bg-muted"></div>
			{/each}
		</div>
	{:else if entries.length === 0}
		<p class="py-4 text-sm text-muted-foreground">Inga sökningar hittades.</p>
	{:else}
		<div class="space-y-3">
			{#each entries as entry (entry.id)}
				<QueueEntryCard
					{entry}
					{courseMap}
					{apiBaseUrl}
					onEdit={openEdit}
					onCancel={(e) => (pendingCancelEntry = e)}
				/>

				<!-- Inline edit form -->
				{#if editingEntry?.id === entry.id}
					<div class="rounded-xl border bg-muted/30 p-4 space-y-4">
						<p class="text-sm text-muted-foreground">
							Datum: {formatTargetDate(entry.target_date)} (kan inte ändras)
						</p>

						<CourseMultiSelect
							bind:selected={editCourseIds}
							{apiBaseUrl}
							storageKey="golfkompis.queue_edit"
							onChange={(ids) => (editCourseIds = ids)}
						/>

						<div class="grid grid-cols-2 gap-3">
							<div class="flex flex-col gap-1.5">
								<Label for="eq-start-{entry.id}">
									<span class="block text-xs leading-none text-muted-foreground">Starttid</span>
									<span>Tidigast <span class="text-xs text-muted-foreground">(valfritt)</span></span>
								</Label>
								<input
									id="eq-start-{entry.id}"
									type="time"
									bind:value={editStart}
									class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-ring focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
								/>
							</div>
							<div class="flex flex-col gap-1.5">
								<Label for="eq-stop-{entry.id}">
									<span class="block text-xs leading-none text-muted-foreground">Sluttid</span>
									<span>Senast <span class="text-xs text-muted-foreground">(valfritt)</span></span>
								</Label>
								<input
									id="eq-stop-{entry.id}"
									type="time"
									bind:value={editStop}
									class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:ring-1 focus-visible:ring-ring focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
								/>
							</div>
						</div>

						<div class="flex flex-col gap-1.5">
							<Label>Antal platser</Label>
							<div class="flex gap-1.5">
								{#each [1, 2, 3, 4] as n (n)}
									<Button
										variant={editSpots === n ? 'default' : 'outline'}
										size="sm"
										class="w-10"
										onclick={() => (editSpots = n)}
									>
										{n}
									</Button>
								{/each}
							</div>
						</div>

						{#if editError}
							<div class="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
								{editError}
							</div>
						{/if}

						<div class="flex gap-2">
							<Button onclick={saveEdit} disabled={editSaving}>
								{editSaving ? 'Sparar…' : 'Spara'}
							</Button>
							<Button variant="ghost" onclick={() => (editingEntry = null)}>Avbryt redigering</Button>
						</div>
					</div>
				{/if}
			{/each}
		</div>
	{/if}
</section>

<!-- Cancel confirmation dialog -->
<AlertDialog.Root bind:open={cancelDialogOpen} onOpenChange={(v) => { if (!v) pendingCancelEntry = null; }}>
	<AlertDialog.Portal>
		<AlertDialog.Overlay />
		<AlertDialog.Content>
			<AlertDialog.Header>
				<AlertDialog.Title>Avbryt sökning?</AlertDialog.Title>
				<AlertDialog.Description>
					{#if pendingCancelEntry}
						Sökningen för {formatTargetDate(pendingCancelEntry.target_date)} tas bort från kön.
					{/if}
				</AlertDialog.Description>
			</AlertDialog.Header>
			<AlertDialog.Footer>
				<AlertDialog.Cancel onclick={() => (pendingCancelEntry = null)}>Behåll</AlertDialog.Cancel>
				<AlertDialog.Action
					class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
					onclick={confirmCancel}
				>
					Avbryt sökning
				</AlertDialog.Action>
			</AlertDialog.Footer>
		</AlertDialog.Content>
	</AlertDialog.Portal>
</AlertDialog.Root>
