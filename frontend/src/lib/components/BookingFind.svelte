<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Label } from '$lib/components/ui/label';
	import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
	import ChevronRightIcon from '@lucide/svelte/icons/chevron-right';
	import Loader2Icon from '@lucide/svelte/icons/loader-2';
	import SearchIcon from '@lucide/svelte/icons/search';
	import TriangleAlertIcon from '@lucide/svelte/icons/triangle-alert';

	import { createApiClient, ApiError, getErrorMessage } from '$lib/api';
	import type { Slot, Course } from '$lib/api';
	import { credentials } from '$lib/auth/credentials.svelte';
	import { todayInTz, formatSlotTime, flexColorStyle } from '$lib/format';
	import CourseMultiSelect from './CourseMultiSelect.svelte';
	import BookSlotDialog from './BookSlotDialog.svelte';

	interface Props {
		apiBaseUrl?: string;
		onBooked?: (slot: Slot) => void;
	}

	let { apiBaseUrl = '', onBooked }: Props = $props();

	type SlotWithCourse = Slot & { course: Course };

	type CourseResult =
		| { course: Course; slots: SlotWithCourse[]; error: null; open: boolean }
		| { course: Course; slots: []; error: string; open: boolean };

	// ── State ────────────────────────────────────────────────────────────────
	let courseIds = $state<string[]>([]);
	let selectedCourses = $state<Course[]>([]);
	// Computed in Stockholm timezone to avoid UTC-midnight off-by-one bugs
	let today = $derived(todayInTz());
	let date = $state(todayInTz());
	let start = $state('');
	let stop = $state('');
	let spots = $state(1);

	let loading = $state(false);
	let searched = $state(false);
	let results = $state<CourseResult[]>([]);

	let bookTarget = $state<SlotWithCourse | null>(null);

	// Track active request to avoid stale abort clobbering a newer search's state
	let currentSearchId = 0;
	let controller: AbortController | null = null;

	// ── Helpers ──────────────────────────────────────────────────────────────
	function slotBookable(slot: Slot): boolean {
		return slot.availablity.bookable && !slot.isLocked;
	}

	function handleCoursesChange(ids: string[], courses: Course[]) {
		courseIds = ids;
		selectedCourses = courses;
	}

	// ── Search ───────────────────────────────────────────────────────────────
	async function search() {
		const creds = credentials.value;
		if (!creds || selectedCourses.length === 0) return;

		controller?.abort();
		controller = new AbortController();
		const signal = controller.signal;

		// Stamp this search so stale completions don't overwrite newer state
		const searchId = ++currentSearchId;

		loading = true;
		searched = true;
		results = [];

		const api = createApiClient({ baseUrl: apiBaseUrl, credentials: creds });

		const settled = await Promise.allSettled(
			selectedCourses.map((course) =>
				api
					.findSlots({
						date,
						courses: [course.CourseID],
						start: start || undefined,
						stop: stop || undefined,
						spots
					})
					.then((slots) =>
						slots
							.map((s): SlotWithCourse => ({ ...s, course }))
							.sort((a, b) => a.time.localeCompare(b.time))
					)
			)
		);

		// Discard results if a newer search has already started
		if (signal.aborted || searchId !== currentSearchId) {
			return;
		}

		results = settled.map((outcome, i): CourseResult => {
			const course = selectedCourses[i]!;
			if (outcome.status === 'fulfilled') {
				return { course, slots: outcome.value, error: null, open: false };
			} else {
				const err = outcome.reason;
				const msg = getErrorMessage(err, {
					not_found: 'Banan hittades inte.',
					unauthorized: 'Ej behörig.',
					default: 'Kunde inte hämtas.',
				});
				return { course, slots: [], error: msg, open: false };
			}
		});

		loading = false;
	}

	function toggleCourse(index: number) {
		const r = results[index];
		if (!r) return;
		// Mutate open flag directly instead of spreading (preserves discriminated-union type)
		results[index] = { ...r, open: !r.open } as CourseResult;
	}

	async function handleBooked(slot: Slot) {
		onBooked?.(slot);
		await search();
	}
</script>

<section class="border rounded-xl p-4">
	<h2 class="mb-4 text-xl font-semibold">Hitta starttider</h2>

	{#if !credentials.value}
		<p class="text-muted-foreground text-sm">Logga in för att söka starttider.</p>
	{:else}
		<!-- Controls -->
		<div class="space-y-4">
			<CourseMultiSelect bind:selected={courseIds} {apiBaseUrl} onChange={handleCoursesChange} />

			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
				<!-- Date -->
				<div class="flex flex-col gap-1.5">
					<Label for="bf-date">Datum</Label>
					<input
						id="bf-date"
						type="date"
						bind:value={date}
						min={today}

						class="border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
					/>
				</div>

				<!-- Spots -->
				<div class="flex flex-col gap-1.5">
					<Label>Antal platser</Label>
					<div class="flex gap-1.5">
						{#each [1, 2, 3, 4] as n (n)}
							<Button
								variant={spots === n ? 'default' : 'outline'}
								size="sm"
								class="w-10"
								onclick={() => (spots = n)}
							>
								{n}
							</Button>
						{/each}
					</div>
				</div>
			</div>

			<!-- Optional time range -->
			<div class="grid grid-cols-2 gap-3">
				<div class="flex flex-col gap-1.5">
					<Label for="bf-start" class="whitespace-nowrap">
						<span class="text-muted-foreground block text-xs leading-none">Starttid</span>
						<span>Tidigast <span class="text-muted-foreground text-xs">(valfritt)</span></span>
					</Label>
					<input
						id="bf-start"
						type="time"
						bind:value={start}
						class="border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
					/>
				</div>
				<div class="flex flex-col gap-1.5">
					<Label for="bf-stop" class="whitespace-nowrap">
						<span class="text-muted-foreground block text-xs leading-none">Starttid</span>
						<span>Senast <span class="text-muted-foreground text-xs">(valfritt)</span></span>
					</Label>
					<input
						id="bf-stop"
						type="time"
						bind:value={stop}
						class="border-input bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
					/>
				</div>
			</div>

			<Button onclick={search} disabled={loading || courseIds.length === 0} class="w-full sm:w-auto">
				{#if loading}
					<Loader2Icon class="mr-2 h-4 w-4 animate-spin" />
					Söker…
				{:else}
					<SearchIcon class="mr-2 h-4 w-4" />
					Sök
				{/if}
			</Button>
		</div>

		<!-- Results -->
		<div class="mt-6">
			{#if loading}
				<!-- Skeletons -->
				<div class="space-y-3">
					{#each [0, 1, 2] as n (n)}
						<div class="bg-muted h-10 w-full animate-pulse rounded-md"></div>
					{/each}
				</div>
			{:else if searched && results.length === 0}
				<p class="text-muted-foreground py-4 text-sm">Inga banor valda.</p>
			{:else if results.length > 0}
				<div class="space-y-2">
					{#each results as result, i (result.course.CourseID)}
						<div class="border rounded-xl overflow-hidden">
							<!-- Course header -->
							<button
								type="button"
								class="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm font-medium transition-colors hover:bg-muted/50"
								onclick={() => toggleCourse(i)}
								aria-expanded={result.open}
							>
								{#if result.open}
									<ChevronDownIcon class="h-4 w-4 shrink-0 text-muted-foreground" />
								{:else}
									<ChevronRightIcon class="h-4 w-4 shrink-0 text-muted-foreground" />
								{/if}
								<span class="flex-1 truncate">
									{result.course.ClubName} – {result.course.CourseName}
								</span>
								{#if result.error}
									<Badge variant="destructive" class="shrink-0 text-xs">
										<TriangleAlertIcon class="mr-1 h-3 w-3" />
										Fel
									</Badge>
								{:else}
									<Badge variant="secondary" class="shrink-0 text-xs">
										{result.slots.filter(s => s.availablity.availableSlots > 0).length} tider
									</Badge>
								{/if}
							</button>

							<!-- Expanded content -->
							{#if result.open}
								{#if result.error}
									<div class="border-t px-3 py-2">
										<p class="text-destructive text-sm">{result.error}</p>
									</div>
								{:else if result.slots.length === 0}
									<div class="border-t px-3 py-2">
										<p class="text-muted-foreground text-sm">Inga tider matchar filtren.</p>
									</div>
								{:else}
									<ul class="divide-y border-t">
										{#each result.slots as slot (slot.id)}
											{@const bookable = slotBookable(slot)}
											{@const fc = flexColorStyle(slot.flexColor)}
											<li>
												<button
													type="button"
													class="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors {bookable
														? 'hover:bg-muted/50 cursor-pointer'
														: 'cursor-not-allowed opacity-50'}"
													disabled={!bookable}
													onclick={() => bookable && (bookTarget = slot)}
												>
													<!-- Time -->
													<span class="w-11 shrink-0 font-mono text-sm tabular-nums">{formatSlotTime(slot.time)}</span>

													<!-- Players + badges -->
													<span class="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
														{#if slot.playersInfo.length > 0}
															<span class="truncate text-sm">{slot.playersInfo.join(', ')}</span>
														{:else}
															<span class="text-muted-foreground text-sm">Tom boll</span>
														{/if}
														{#if slot.nineHoleBookingAavailable}
															<Badge variant="secondary" class="shrink-0 px-1 py-0 text-xs">9</Badge>
														{/if}
														{#if fc}
															<span
																class="inline-block h-2.5 w-2.5 shrink-0 rounded-full ring-1 ring-black/10"
																style="background-color: {fc}"
																title="Flex: {slot.flexColor}"
															></span>
														{/if}
														{#if slot.maximumHcpPerSlot !== null}
															<Badge variant="outline" class="shrink-0 px-1 py-0 text-xs text-amber-600">
																HCP ≤{slot.maximumHcpPerSlot}
															</Badge>
														{/if}
													</span>

													<!-- Availability + price -->
													<span class="flex shrink-0 flex-col items-end gap-0.5">
														<Badge
															variant={slot.availablity.availableSlots > 0 ? 'default' : 'secondary'}
															class="text-xs"
														>
															{slot.availablity.availableSlots}/{slot.availablity.maxNumberOfSlotBookings}
														</Badge>
														{#if slot.price.greenfee !== null}
															<span class="text-muted-foreground text-xs">{slot.price.greenfee} kr</span>
														{/if}
													</span>
												</button>
											</li>
										{/each}
									</ul>
								{/if}
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</section>

<BookSlotDialog bind:slot={bookTarget} {date} {apiBaseUrl} course={bookTarget?.course} onBooked={handleBooked} />
