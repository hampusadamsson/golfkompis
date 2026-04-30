<script lang="ts">
	import {
		Dialog,
		DialogContent,
		DialogHeader,
		DialogTitle,
		DialogDescription,
		DialogFooter
	} from '$lib/components/ui/dialog';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import Loader2Icon from '@lucide/svelte/icons/loader-2';
	import TriangleAlertIcon from '@lucide/svelte/icons/triangle-alert';
	import CheckIcon from '@lucide/svelte/icons/check';

	import { createApiClient, ApiError, getErrorMessage } from '$lib/api';
	import type { Slot, Course } from '$lib/api';
	import { credentials } from '$lib/auth/credentials.svelte';
	import { formatDateLong, formatSlotTime, flexColorStyle } from '$lib/format';

	interface Props {
		slot: Slot | null;
		date: string;
		course?: Course;
		apiBaseUrl?: string;
		onBooked?: (slot: Slot) => void;
	}

	let { slot = $bindable(null), date, course, apiBaseUrl = '', onBooked }: Props = $props();

	let booking = $state(false);
	let booked = $state(false);
	let bookedSlot = $state<Slot | null>(null);
	let errorMessage = $state<string | null>(null);

	let open = $derived(slot !== null || booked);

	function close() {
		slot = null;
		booked = false;
		bookedSlot = null;
		errorMessage = null;
	}

	function handleOpenChange(value: boolean) {
		if (!value && !booking) {
			close();
		}
	}

	async function handleBook() {
		if (!slot) return;
		const creds = credentials.value;
		if (!creds) return;

		// Freeze the slot reference now — the parent may null out `slot` before
		// the async request completes (e.g. rapid reopen scenario).
		const targetSlot = slot;

		booking = true;
		errorMessage = null;

		const api = createApiClient({ baseUrl: apiBaseUrl, credentials: creds });
		try {
			await api.book({ slot_id: targetSlot.id });
			bookedSlot = targetSlot;
			booked = true;
			slot = null;
			onBooked?.(targetSlot);
		} catch (err) {
			errorMessage = getErrorMessage(err);
		} finally {
			booking = false;
		}
	}
</script>

<Dialog {open} onOpenChange={handleOpenChange}>
	<DialogContent class="sm:max-w-md">
		{#if booked && bookedSlot}
			<!-- Success state -->
			<DialogHeader>
				<DialogTitle class="flex items-center gap-2 text-green-600">
					<CheckIcon class="h-5 w-5" />
					Starttid bokad!
				</DialogTitle>
			<DialogDescription>
				{formatSlotTime(bookedSlot.time)} &mdash; {formatDateLong(date)}{#if course} &middot; {course.ClubName} – {course.CourseName}{/if}
			</DialogDescription>
			</DialogHeader>
			<p class="text-muted-foreground py-2 text-sm">
				Din bokning är bekräftad. Se <strong>Kommande bokningar</strong> nedan.
			</p>
			<DialogFooter>
				<Button onclick={close}>Stäng</Button>
			</DialogFooter>
		{:else if slot}
			<!-- Booking form -->
			<DialogHeader>
				<DialogTitle class="flex items-center gap-2">
				<span>Boka starttid</span>
				{#if slot.nineHoleBookingAavailable}
					<Badge variant="secondary" class="text-xs">9 hål</Badge>
					{/if}
					{#if slot.flexColor}
						{@const fc = flexColorStyle(slot.flexColor)}
						{#if fc}
							<span
								class="inline-block h-3 w-3 rounded-full ring-1 ring-black/10"
								style="background-color: {fc}"
								title="Flex: {slot.flexColor}"
							></span>
						{/if}
					{/if}
				</DialogTitle>
			<DialogDescription>
				{formatSlotTime(slot.time)} &mdash; {formatDateLong(date)}{#if course} &middot; {course.ClubName} – {course.CourseName}{/if}
			</DialogDescription>
			</DialogHeader>

			<div class="space-y-3 py-2 text-sm">
				<!-- Players in ball -->
				<div>
					<p class="text-muted-foreground mb-1 text-xs font-medium uppercase tracking-wide">
						Spelare i bollen
					</p>
					{#if slot.playersInfo.length > 0}
						<ul class="space-y-0.5">
							{#each slot.playersInfo as player, i (i)}
								<li>{player}</li>
							{/each}
						</ul>
					{:else}
						<p class="text-muted-foreground">Tom boll</p>
					{/if}
				</div>

				<!-- Availability -->
				<div class="flex items-center gap-4">
					<div>
						<p class="text-muted-foreground mb-0.5 text-xs font-medium uppercase tracking-wide">
							Lediga platser
						</p>
						<p>{slot.availablity.availableSlots} / {slot.availablity.maxNumberOfSlotBookings}</p>
					</div>
					{#if slot.price.greenfee !== null}
						<div>
							<p class="text-muted-foreground mb-0.5 text-xs font-medium uppercase tracking-wide">
								Greenfee
							</p>
							<p>{slot.price.greenfee} kr</p>
						</div>
					{/if}
				</div>

				<!-- HCP warning -->
				{#if slot.maximumHcpPerSlot !== null}
					<div class="bg-muted/60 flex items-start gap-2 rounded-md px-3 py-2 text-xs">
						<TriangleAlertIcon class="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
						<span>Max HCP för denna tid: {slot.maximumHcpPerSlot}</span>
					</div>
				{/if}

				<!-- Error -->
				{#if errorMessage}
					<Alert variant="destructive">
						<AlertDescription>{errorMessage}</AlertDescription>
					</Alert>
				{/if}
			</div>

			<DialogFooter class="gap-2 sm:gap-0">
				<Button variant="outline" onclick={() => handleOpenChange(false)} disabled={booking}>
					Avbryt
				</Button>
				<Button onclick={handleBook} disabled={booking}>
					{#if booking}
						<Loader2Icon class="mr-2 h-4 w-4 animate-spin" />
						Bokar…
					{:else}
						Bekräfta bokning
					{/if}
				</Button>
			</DialogFooter>
		{/if}
	</DialogContent>
</Dialog>
