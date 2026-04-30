<script lang="ts">
	import {
		AlertDialog,
		AlertDialogContent,
		AlertDialogHeader,
		AlertDialogTitle,
		AlertDialogDescription,
		AlertDialogFooter,
		AlertDialogCancel,
		AlertDialogAction
	} from '$lib/components/ui/alert-dialog';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import Loader2Icon from '@lucide/svelte/icons/loader-2';
	import TriangleAlertIcon from '@lucide/svelte/icons/triangle-alert';
	import XIcon from '@lucide/svelte/icons/x';

	import { createApiClient, getErrorMessage } from '$lib/api';
	import type { Booking } from '$lib/api';
	import { credentials } from '$lib/auth/credentials.svelte';
	import { dateFmt, formatSlotTime } from '$lib/format';

	interface Props {
		apiBaseUrl?: string;
		/** Bump to trigger a re-fetch. */
		refreshKey?: number;
	}

	let { apiBaseUrl = '', refreshKey = 0 }: Props = $props();

	// ── State ────────────────────────────────────────────────────────────────
	let loading = $state(false);
	let errorMessage = $state<string | null>(null);
	let upcoming = $state<Booking[]>([]);
	let cancellingId = $state<string | null>(null);
	let confirmTarget = $state<Booking | null>(null);
	let dialogOpen = $state(false);

	// ── Fetch ────────────────────────────────────────────────────────────────
	$effect(() => {
		const creds = credentials.value;
		// Read refreshKey to register it as a reactive dependency
		void refreshKey;
		if (!creds) return;

		const controller = new AbortController();
		loading = true;
		errorMessage = null;

		const api = createApiClient({ baseUrl: apiBaseUrl, credentials: creds });
		api
			.listBookings({}, { signal: controller.signal })
			.then((data) => {
				upcoming = [...data].sort((a, b) => a.slotTimeAsDate.localeCompare(b.slotTimeAsDate));
			})
			.catch((err) => {
			if ((err as { name?: string }).name === 'AbortError') return;
			errorMessage = getErrorMessage(err);
		})
			.finally(() => {
				loading = false;
			});

		return () => controller.abort();
	});

	// ── Cancel ───────────────────────────────────────────────────────────────
	function requestCancel(round: Booking) {
		confirmTarget = round;
		dialogOpen = true;
	}

	async function handleConfirmCancel() {
		const round = confirmTarget;
		if (!round?.bookingInfo?.bookingId) return;

		const bookingId = round.bookingInfo.bookingId;

		const creds = credentials.value;
		// Guard before setting cancellingId so the button doesn't get stuck
		// if we return early due to missing credentials.
		if (!creds) return;

		cancellingId = bookingId;

		const api = createApiClient({ baseUrl: apiBaseUrl, credentials: creds });
		try {
			await api.cancelBooking(bookingId);
			upcoming = upcoming.filter((b) => b.bookingInfo?.bookingId !== bookingId);
		} catch (err) {
			errorMessage = getErrorMessage(err, {
				not_found: 'Bokningen är redan avbokad eller hittas inte.',
				default: 'Kunde inte avboka.',
			});
		} finally {
			cancellingId = null;
			confirmTarget = null;
			dialogOpen = false;
		}
	}
</script>

<div class="border rounded-xl p-4 w-full">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-xl font-semibold">Kommande bokningar</h2>
		{#if !loading && !errorMessage && credentials.value}
			<Badge variant="secondary" class="text-xs">{upcoming.length} bokningar</Badge>
		{/if}
	</div>

	{#if !credentials.value}
		<p class="text-muted-foreground text-sm">Logga in för att se dina kommande bokningar.</p>
	{:else if loading}
		<ul class="space-y-2">
			{#each { length: 3 }, i (i)}
				<li class="bg-muted h-9 animate-pulse rounded"></li>
			{/each}
		</ul>
	{:else if errorMessage}
		<Alert variant="destructive">
			<TriangleAlertIcon class="h-4 w-4" />
			<AlertDescription>{errorMessage}</AlertDescription>
		</Alert>
	{:else if upcoming.length === 0}
		<p class="text-muted-foreground text-sm">Inga kommande bokningar.</p>
	{:else}
		<ul class="divide-border divide-y text-sm">
			{#each upcoming as round (round.slotId)}
				<li class="flex items-center gap-3 py-2">
					<!-- Date + time -->
					<span class="text-muted-foreground w-32 shrink-0 tabular-nums">
						{dateFmt.format(new Date(round.slotTimeAsDate))}
						<span class="ml-1 opacity-70">{formatSlotTime(round.slotTime)}</span>
					</span>

					<!-- Course -->
					<span class="flex min-w-0 flex-1 items-center gap-1.5 truncate">
						<span class="truncate">{round.courseName}</span>
						{#if round.roundType}
							<Badge variant="secondary" class="shrink-0 px-1.5 py-0 text-xs">
								{round.roundType}
							</Badge>
						{/if}
					</span>

					<!-- Cancel -->
					<span class="shrink-0">
						{#if round.bookingInfo?.bookingId}
							<Button
								size="sm"
								variant="ghost"
								class="h-7 w-7 p-0"
								aria-label="Avboka"
								disabled={cancellingId === round.bookingInfo.bookingId}
								onclick={() => requestCancel(round)}
							>
								{#if cancellingId === round.bookingInfo.bookingId}
									<Loader2Icon class="h-4 w-4 animate-spin" />
								{:else}
									<XIcon class="h-4 w-4" />
								{/if}
							</Button>
						{:else}
							<span class="text-muted-foreground">—</span>
						{/if}
					</span>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<!-- Cancel confirmation dialog -->
<AlertDialog bind:open={dialogOpen}>
	<AlertDialogContent>
		<AlertDialogHeader>
			<AlertDialogTitle>Avboka?</AlertDialogTitle>
			<AlertDialogDescription>
				{#if confirmTarget}
					{confirmTarget.courseName} · {dateFmt.format(new Date(confirmTarget.slotTimeAsDate))}
					{formatSlotTime(confirmTarget.slotTime)}
				{/if}
				<br />Detta går inte att ångra.
			</AlertDialogDescription>
		</AlertDialogHeader>
		<AlertDialogFooter>
			<AlertDialogCancel>Behåll bokning</AlertDialogCancel>
			<AlertDialogAction onclick={handleConfirmCancel}>Avboka</AlertDialogAction>
		</AlertDialogFooter>
	</AlertDialogContent>
</AlertDialog>
