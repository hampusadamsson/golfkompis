<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import CheckIcon from '@lucide/svelte/icons/check';
	import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
	import SearchIcon from '@lucide/svelte/icons/search';
	import XIcon from '@lucide/svelte/icons/x';

	import { onMount } from 'svelte';
	import { createApiClient } from '$lib/api';
	import type { Course } from '$lib/api';

	const STORAGE_KEY = 'golfkompis.selected_courses';
	const DISPLAY_CAP = 200;

	interface Props {
		/** Currently selected CourseIDs. Bindable. */
		selected?: string[];
		/** Called whenever selection changes. */
		onChange?: (selectedIds: string[], selectedCourses: Course[]) => void;
		/** Persist selection to localStorage. Default: true (uses built-in key). */
		storageKey?: string | false;
		/** Limit to 18-hole courses only. Default false. */
		only18?: boolean;
		/** Max chips visible before "+N more" overflow. Default 5. */
		maxVisibleChips?: number;
		/** Toggle label for 18-hole filter. */
		placeholder?: string;
		apiBaseUrl?: string;
	}

	let {
		selected = $bindable([]),
		onChange,
		storageKey = STORAGE_KEY,
		only18 = $bindable(false),
		maxVisibleChips = 5,
		placeholder = 'Sök banor…',
		apiBaseUrl = ''
	}: Props = $props();

	// ── Course catalogue ──────────────────────────────────────────────────────
	let allCourses = $state<Course[]>([]);
	let loadError = $state<string | null>(null);
	let loading = $state(false);

	$effect(() => {
		const controller = new AbortController();
		loading = true;
		loadError = null;

		const api = createApiClient({ baseUrl: apiBaseUrl });
		api
			.listCourses({ only_18: only18 }, { signal: controller.signal })
			.then((data) => {
				allCourses = data.sort((a, b) =>
					`${a.ClubName} ${a.CourseName}`.localeCompare(`${b.ClubName} ${b.CourseName}`, 'sv')
				);
			})
			.catch((err) => {
				if ((err as { name?: string }).name === 'AbortError') return;
				loadError = 'Kunde inte hämta banor.';
			})
			.finally(() => {
				loading = false;
			});

		return () => controller.abort();
	});

	// ── Persistence ───────────────────────────────────────────────────────────
	// Load from storage once on mount (not reactive — avoids infinite loop)
	onMount(() => {
		if (!storageKey) return;
		if (selected.length > 0) return;
		try {
			const raw = localStorage.getItem(storageKey as string);
			if (raw) {
				const parsed = JSON.parse(raw);
				if (Array.isArray(parsed) && parsed.every((v) => typeof v === 'string')) {
					selected = parsed;
				}
			}
		} catch {
			// ignore corrupted storage
		}
	});

	function persist(ids: string[]) {
		if (!storageKey || typeof window === 'undefined') return;
		localStorage.setItem(storageKey as string, JSON.stringify(ids));
	}

	// ── Derived helpers ───────────────────────────────────────────────────────
	const selectedSet = $derived(new Set(selected));

	const courseMap = $derived(new Map<string, Course>(allCourses.map((c) => [c.CourseID, c])));

	const selectedCourses = $derived(
		selected.flatMap((id) => {
			const c = courseMap.get(id);
			return c ? [c] : [];
		})
	);

	// Notify parent whenever selection or catalogue changes (covers rehydration on mount).
	$effect(() => {
		if (allCourses.length === 0) return;
		onChange?.(selected, selectedCourses);
	});

	function label(c: Course) {
		return `${c.ClubName} (${c.CourseName})`;
	}

	// ── Search + filter ───────────────────────────────────────────────────────
	let query = $state('');

	const filtered = $derived.by(() => {
		const q = query.trim().toLowerCase();
		if (!q) return allCourses;
		return allCourses.filter((c) => `${c.ClubName} ${c.CourseName}`.toLowerCase().includes(q));
	});

	const displayed = $derived(filtered.slice(0, DISPLAY_CAP));
	const overflow = $derived(filtered.length - displayed.length);

	// ── Dropdown open/close ───────────────────────────────────────────────────
	let open = $state(false);
	let containerEl = $state<HTMLDivElement | null>(null);

	$effect(() => {
		if (!open) return;

		function handleOutside(e: MouseEvent) {
			if (containerEl && !containerEl.contains(e.target as Node)) {
				open = false;
			}
		}

		function handleEsc(e: KeyboardEvent) {
			if (e.key === 'Escape') open = false;
		}

		document.addEventListener('mousedown', handleOutside);
		document.addEventListener('keydown', handleEsc);
		return () => {
			document.removeEventListener('mousedown', handleOutside);
			document.removeEventListener('keydown', handleEsc);
		};
	});

	// ── Toggle selection ──────────────────────────────────────────────────────
	function toggle(courseId: string) {
		if (selectedSet.has(courseId)) {
			selected = selected.filter((id) => id !== courseId);
		} else {
			selected = [...selected, courseId];
		}
		persist(selected);
	}

	function deselect(courseId: string) {
		selected = selected.filter((id) => id !== courseId);
		persist(selected);
	}

	// ── Chip overflow ─────────────────────────────────────────────────────────
	let chipsExpanded = $state(false);
	const visibleChips = $derived(
		chipsExpanded ? selectedCourses : selectedCourses.slice(0, maxVisibleChips)
	);
	const hiddenCount = $derived(selectedCourses.length - maxVisibleChips);
</script>

<div class="relative w-full" bind:this={containerEl}>
	<!-- Selected chips -->
	{#if selectedCourses.length > 0}
		<div class="mb-2 flex flex-wrap gap-1.5">
			{#each visibleChips as course (course.CourseID)}
				<Badge variant="secondary" class="flex items-center gap-1 pr-1">
					<span class="max-w-[180px] truncate text-xs">{label(course)}</span>
					<button
						type="button"
						aria-label="Ta bort {label(course)}"
						class="ml-0.5 transition-colors hover:text-destructive"
						onclick={() => deselect(course.CourseID)}
					>
						<XIcon class="h-3 w-3" />
					</button>
				</Badge>
			{/each}
			{#if !chipsExpanded && hiddenCount > 0}
				<button
					type="button"
					class="text-xs text-muted-foreground underline hover:text-foreground"
					onclick={() => (chipsExpanded = true)}
				>
					+{hiddenCount} till
				</button>
			{:else if chipsExpanded && hiddenCount > 0}
				<button
					type="button"
					class="text-xs text-muted-foreground underline hover:text-foreground"
					onclick={() => (chipsExpanded = false)}
				>
					visa färre
				</button>
			{/if}
		</div>
	{/if}

	<!-- Search input -->
	<div class="relative">
		<SearchIcon
			class="pointer-events-none absolute top-1/2 left-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground"
		/>
		<Input
			class="pr-8 pl-8"
			{placeholder}
			disabled={loading}
			bind:value={query}
			onfocus={() => (open = true)}
			onclick={() => (open = true)}
		/>
		<ChevronDownIcon
			class="pointer-events-none absolute top-1/2 right-2.5 h-4 w-4 -translate-y-1/2 text-muted-foreground transition-transform {open
				? 'rotate-180'
				: ''}"
		/>
	</div>

	<!-- 18-hole toggle -->
	<div class="mt-2 flex items-center gap-2 p-2">
		<label class="flex cursor-pointer items-center gap-1.5 text-sm select-none">
			<input
				type="checkbox"
				class="accent-primary"
				bind:checked={only18}
				onchange={() => {
					// deselect any 9-hole courses that are now hidden
					if (only18) {
						selected = selected.filter((id) => {
							const c = courseMap.get(id);
							return c ? !c.IsNineHoleCourse : true;
						});
						persist(selected);
					}
				}}
			/>
			Endast 18 hål
		</label>
	</div>

	{#if loadError}
		<p class="mt-1 text-xs text-destructive">{loadError}</p>
	{/if}

	<!-- Dropdown -->
	{#if open}
		<div
			class="absolute top-full z-50 mt-1 max-h-80 w-full overflow-y-auto rounded-md border border-border bg-popover shadow-md"
			role="listbox"
			aria-multiselectable="true"
		>
			{#if loading}
			<div class="px-3 py-6 text-center text-sm text-muted-foreground">Hämtar banor…</div>
		{:else if displayed.length === 0}
			<div class="px-3 py-6 text-center text-sm text-muted-foreground">Inga banor hittades.</div>
			{:else}
				{#each displayed as course (course.CourseID)}
					{@const isSelected = selectedSet.has(course.CourseID)}
					<button
						type="button"
						role="option"
						aria-selected={isSelected}
						class="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-accent {isSelected
							? 'bg-accent/50'
							: ''}"
						onclick={() => toggle(course.CourseID)}
					>
						<span class="flex h-4 w-4 shrink-0 items-center justify-center">
							{#if isSelected}
								<CheckIcon class="h-3.5 w-3.5 text-primary" />
							{/if}
						</span>
						<span class="truncate">{label(course)}</span>
						{#if course.IsNineHoleCourse}
							<Badge variant="outline" class="ml-auto shrink-0 px-1 py-0 text-xs">9</Badge>
						{/if}
					</button>
				{/each}
				{#if overflow > 0}
					<div class="border-t px-3 py-2 text-center text-xs text-muted-foreground">
						{overflow} till — förfina sökningen för att se dem
					</div>
				{/if}
			{/if}
		</div>
	{/if}
</div>
