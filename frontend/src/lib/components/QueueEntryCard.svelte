<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
	import ChevronRightIcon from '@lucide/svelte/icons/chevron-right';

	import type { QueueEntry, Course, Slot } from '$lib/api';
	import { formatSlotTime, flexColorStyle } from '$lib/format';
	import BookSlotDialog from './BookSlotDialog.svelte';

	interface Props {
		entry: QueueEntry;
		courseMap: Map<string, Course>;
		onEdit: (entry: QueueEntry) => void;
		onCancel: (entry: QueueEntry) => void;
		apiBaseUrl?: string;
	}

	let { entry, courseMap, onEdit, onCancel, apiBaseUrl = '' }: Props = $props();

	let slotsOpen = $state(false);
	let bookTarget = $state<Slot | null>(null);

	function formatTargetDate(dateStr: string): string {
		return new Date(dateStr + 'T12:00:00').toLocaleDateString('sv-SE', {
			weekday: 'short',
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	function formatChecked(iso: string | null): string {
		if (!iso) return 'Ej kontrollerad';
		return new Date(iso).toLocaleString('sv-SE', {
			dateStyle: 'short',
			timeStyle: 'short'
		});
	}

	function courseName(id: string): string {
		const c = courseMap.get(id);
		if (c) return `${c.ClubName} (${c.CourseName})`;
		return id.slice(0, 8) + '…';
	}

	const timeWindow = $derived(
		entry.start_time || entry.stop_time
			? `${entry.start_time?.slice(0, 5) ?? '?'} – ${entry.stop_time?.slice(0, 5) ?? '?'}`
			: 'Hela dagen'
	);
</script>

<div class="rounded-xl border p-4 space-y-3">
	<!-- Row 1: date + status badge -->
	<div class="flex items-center justify-between gap-2">
		<span class="font-semibold">{formatTargetDate(entry.target_date)}</span>
		{#if entry.status === 'active'}
			<Badge variant="secondary">Aktiv</Badge>
		{:else if entry.status === 'matched'}
			<Badge class="bg-green-100 text-green-800 border-green-200">Matchad</Badge>
		{:else if entry.status === 'expired'}
			<Badge variant="destructive">Utgången</Badge>
		{:else}
			<Badge variant="outline">Avbruten</Badge>
		{/if}
	</div>

	<!-- Row 2: time window + spots -->
	<div class="flex items-center gap-2 text-sm">
		<span class="text-muted-foreground">{timeWindow}</span>
		<Badge variant="outline" class="text-xs">
			{entry.min_spots} plats{entry.min_spots > 1 ? 'er' : ''}
		</Badge>
	</div>

	<!-- Row 3: course chips -->
	<div class="flex flex-wrap gap-1">
		{#each entry.course_ids as id (id)}
			<span class="rounded-full border bg-muted px-2 py-0.5 text-xs">{courseName(id)}</span>
		{/each}
	</div>

	<!-- Row 4: footer -->
	<div class="text-xs text-muted-foreground">
		Kontrollerad: {formatChecked(entry.last_checked_at)}{#if entry.check_count > 0}&ensp;({entry.check_count} kontroller){/if}
	</div>

	<!-- Row 5: matched slots (collapsible) -->
	{#if entry.matched_slots && entry.matched_slots.length > 0}
		<div>
			<button
				type="button"
				class="flex items-center gap-1 text-sm font-medium hover:underline"
				onclick={() => (slotsOpen = !slotsOpen)}
			>
				{#if slotsOpen}
					<ChevronDownIcon class="h-4 w-4" />
				{:else}
					<ChevronRightIcon class="h-4 w-4" />
				{/if}
				Matchade tider ({entry.matched_slots.length})
			</button>
			{#if slotsOpen}
				<ul class="mt-2 divide-y rounded-md border">
					{#each entry.matched_slots as slot (slot.id)}
						{@const fc = flexColorStyle(slot.flexColor)}
						<li>
							<button
								type="button"
								class="flex w-full items-center gap-3 px-3 py-2 text-left text-sm transition-colors hover:bg-muted/50 {slot.availablity.bookable && !slot.isLocked ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}"
								disabled={!slot.availablity.bookable || slot.isLocked}
								onclick={() => { if (slot.availablity.bookable && !slot.isLocked) bookTarget = slot; }}
							>
								<span class="w-11 shrink-0 font-mono tabular-nums">{formatSlotTime(slot.time)}</span>
								<span class="flex flex-1 items-center gap-1.5">
									{#if fc}
										<span class="inline-block h-2.5 w-2.5 rounded-full ring-1 ring-black/10" style="background-color: {fc}"></span>
									{/if}
								</span>
								<span class="flex shrink-0 flex-col items-end gap-0.5">
									<Badge variant={slot.availablity.availableSlots > 0 ? 'default' : 'secondary'} class="text-xs">
										{slot.availablity.availableSlots}/{slot.availablity.maxNumberOfSlotBookings}
									</Badge>
									{#if slot.price.greenfee !== null}
										<span class="text-xs text-muted-foreground">{slot.price.greenfee} kr</span>
									{/if}
								</span>
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</div>
	{/if}

	<!-- Row 6: actions (active only) -->
	{#if entry.status === 'active'}
		<div class="flex gap-2">
			<Button variant="outline" size="sm" onclick={() => onEdit(entry)}>Redigera</Button>
			<Button
				variant="outline"
				size="sm"
				class="border-destructive/50 text-destructive hover:bg-destructive/10"
				onclick={() => onCancel(entry)}
			>
				Avbryt
			</Button>
		</div>
	{/if}
</div>

<BookSlotDialog
	bind:slot={bookTarget}
	date={entry.target_date}
	{apiBaseUrl}
	onBooked={() => { bookTarget = null; }}
/>
