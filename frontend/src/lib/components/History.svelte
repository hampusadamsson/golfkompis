<script lang="ts">
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Badge } from '$lib/components/ui/badge';
	import TriangleAlertIcon from '@lucide/svelte/icons/triangle-alert';

	import { createApiClient, getErrorMessage } from '$lib/api';
	import type { Booking } from '$lib/api';
	import { credentials } from '$lib/auth/credentials.svelte';
	import { dateFmt, formatSlotTime, todayInTz } from '$lib/format';

	interface Props {
		apiBaseUrl?: string;
	}

	let { apiBaseUrl = '' }: Props = $props();

	// ── Date range: last 12 months ───────────────────────────────────────────
	const to = todayInTz();
	const from = (() => {
		// eslint-disable-next-line svelte/prefer-svelte-reactivity -- not a reactive value; used only once for date calc
		const d = new Date();
		d.setFullYear(d.getFullYear() - 1);
		// Use Intl to get the date in Stockholm timezone (same approach as todayInTz)
		return new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Stockholm' }).format(d);
	})();

	// ── State ────────────────────────────────────────────────────────────────
	let loading = $state(false);
	let errorMessage = $state<string | null>(null);
	let rounds = $state<Booking[]>([]);

	// ── Fetch ────────────────────────────────────────────────────────────────
	$effect(() => {
		const creds = credentials.value;
		if (!creds) return;

		const controller = new AbortController();
		loading = true;
		errorMessage = null;

		const api = createApiClient({ baseUrl: apiBaseUrl, credentials: creds });
		api
			.getHistory({ from, to }, { signal: controller.signal })
			.then((data) => {
				rounds = [...data].sort(
					(a, b) => b.slotTimeAsDate.localeCompare(a.slotTimeAsDate)
				);
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
</script>

<div class="border rounded-xl p-4 w-full">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="text-xl font-semibold">Rundor – senaste 12 månaderna</h2>
		{#if !loading && !errorMessage && credentials.value}
			<Badge variant="secondary" class="text-xs">{rounds.length} rundor</Badge>
		{/if}
	</div>

	{#if !credentials.value}
		<p class="text-muted-foreground text-sm">Logga in för att se din rundhistorik.</p>
	{:else if loading}
		<ul class="space-y-2">
			{#each { length: 5 }, i (i)}
				<li class="bg-muted h-9 animate-pulse rounded"></li>
			{/each}
		</ul>
	{:else if errorMessage}
		<Alert variant="destructive">
			<TriangleAlertIcon class="h-4 w-4" />
			<AlertDescription>{errorMessage}</AlertDescription>
		</Alert>
	{:else if rounds.length === 0}
		<p class="text-muted-foreground text-sm">Inga rundor de senaste 12 månaderna.</p>
	{:else}
		<ul class="divide-border divide-y text-sm">
			{#each rounds as round (round.slotId)}
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

					<!-- Score -->
					<span class="shrink-0 tabular-nums">
						{#if round.bookingInfo?.points != null}
							<Badge class="px-1.5 py-0 text-xs">{round.bookingInfo.points} p</Badge>
						{:else if round.bookingInfo?.hcpResult}
							<span class="text-muted-foreground text-xs">HCP {round.bookingInfo.hcpResult}</span>
						{:else}
							<span class="text-muted-foreground">—</span>
						{/if}
					</span>
				</li>
			{/each}
		</ul>
	{/if}
</div>
