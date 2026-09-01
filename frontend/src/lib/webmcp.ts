/**
 * WebMCP integration — https://developer.chrome.com/docs/ai/webmcp
 *
 * Registers Golfkompis capabilities as structured tools on
 * `document.modelContext` so AI agents (ChatGPT's in-app browser, Chrome 149+
 * with WebMCP enabled) can call them directly instead of scraping the UI.
 *
 * Tools are a progressive enhancement: registration is skipped entirely when
 * the API is unavailable, and every tool handles unauthenticated callers with
 * a clear message instead of throwing.
 *
 * Tool results are human/agent-readable strings; slot and booking identifiers
 * are always included so an agent can chain tools (search → book → cancel).
 */

import { createApiClient, ApiError } from './api/index.js';
import type { ApiClient } from './api/index.js';
import type { Course, Slot, Booking, QueueEntry } from './api/types.js';

// ── WebMCP API surface (minimal ambient typing) ─────────────────────────────

export interface WebMCPToolAnnotations {
	readOnlyHint?: boolean;
	untrustedContentHint?: boolean;
}

export interface WebMCPTool {
	name: string;
	description: string;
	title?: string;
	inputSchema: Record<string, unknown>;
	annotations?: WebMCPToolAnnotations;
	execute: (input: Record<string, unknown>, opts: { signal: AbortSignal }) => Promise<string>;
}

export interface ModelContext {
	registerTool(
		tool: WebMCPTool,
		options?: { signal?: AbortSignal; exposedTo?: string[] }
	): Promise<void>;
}

declare global {
	interface Document {
		readonly modelContext?: ModelContext;
	}
}

// ── Input coercion helpers ──────────────────────────────────────────────────

function asString(input: Record<string, unknown>, key: string): string {
	const v = input[key];
	return typeof v === 'string' ? v : String(v ?? '');
}

function asStringArray(input: Record<string, unknown>, key: string): string[] {
	const v = input[key];
	if (Array.isArray(v)) return v.map(String);
	if (typeof v === 'string' && v.length > 0) return [v];
	return [];
}

function asOptionalNumber(input: Record<string, unknown>, key: string): number | undefined {
	const v = input[key];
	if (v === undefined || v === null || v === '') return undefined;
	const n = Number(v);
	return Number.isFinite(n) ? n : undefined;
}

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

// ── Formatting helpers (exported for unit tests) ────────────────────────────

/** Normalize a club/course name for fuzzy matching. */
export function normalizeName(name: string): string {
	return name
		.toLowerCase()
		.replace(/[åä]/g, 'a')
		.replace(/ö/g, 'o')
		.replace(/[^a-z0-9]+/g, ' ')
		.trim();
}

/**
 * Resolve free-text club/course queries (from an agent) to catalogue courses.
 * A query matches if it is a substring of the club or course name, or of the
 * normalized forms. Returns unmatched queries so tools can explain failures.
 */
export function resolveCourses(
	catalogue: Course[],
	queries: string[]
): { matched: Course[]; missing: string[] } {
	const missing: string[] = [];
	const picked = new Map<string, Course>();

	for (const q of queries) {
		const norm = normalizeName(q);
		let hits = catalogue.filter(
			(c) => normalizeName(c.ClubName).includes(norm) || normalizeName(c.CourseName).includes(norm)
		);
		if (hits.length === 0) {
			missing.push(q);
			continue;
		}
		// Prefer exact normalized equality, then 18-hole courses, then alphabetical.
		hits = hits.sort((a, b) => {
			const eq = (c: Course) => (normalizeName(c.CourseName) === norm ? 0 : 1);
			return (
				eq(a) - eq(b) ||
				Number(a.IsNineHoleCourse) - Number(b.IsNineHoleCourse) ||
				a.ClubName.localeCompare(b.ClubName)
			);
		});
		picked.set(hits[0].CourseID, hits[0]);
	}

	return { matched: [...picked.values()], missing };
}

/** Render a compact, agent-friendly tee-time list for one course group. */
export function formatSlotGroups(groups: { course: string; slots: Slot[] }[]): string {
	const sections = groups.filter((g) => g.slots.length > 0);
	if (sections.length === 0) return 'No available tee times matched the search.';
	return sections
		.map((g) => {
			const lines = g.slots.map((s) => {
				const time = s.time.slice(11, 16);
				const spots = s.availablity.availableSlots;
				const fee = s.price.greenfee !== null ? ` — ${s.price.greenfee} SEK` : '';
				return `${time} · ${spots} spot${spots === 1 ? '' : 's'}${fee} · slot_id: ${s.id}`;
			});
			return `${g.course}:\n${lines.join('\n')}`;
		})
		.join('\n\n');
}

/** Render a compact booking list. */
export function formatBookings(bookings: Booking[]): string {
	if (bookings.length === 0) return 'No upcoming bookings.';
	return bookings
		.map((b) => {
			const bookingId = b.bookingInfo?.bookingId ?? '(unconfirmed)';
			const time = b.slotTime.slice(11, 16);
			return `${b.slotTimeAsDate} ${time} · ${b.clubName} · ${b.courseName} · booking_id: ${bookingId}`;
		})
		.join('\n');
}

/** Render the tee-time watch queue. */
export function formatQueue(
	entries: QueueEntry[],
	courseName: (courseId: string) => string
): string {
	if (entries.length === 0) return 'No queue watches. Use add_queue_watch to create one.';
	return entries
		.map((e) => {
			const courses = e.course_ids.map(courseName).join(', ');
			const window =
				e.start_time || e.stop_time
					? ` between ${e.start_time ?? 'open'} and ${e.stop_time ?? 'close'}`
					: '';
			return `${e.target_date} · ${courses}${window} · min ${e.min_spots} spot(s) · status: ${e.status} · watch_id: ${e.id}`;
		})
		.join('\n');
}

// ── Error handling ──────────────────────────────────────────────────────────

const NOT_LOGGED_IN =
	'Not logged in. Open Golfkompis and log in first (registration is instant), then try again.';

async function toolGuard(signal: AbortSignal, fn: () => Promise<string>): Promise<string> {
	try {
		return await fn();
	} catch (err) {
		if (signal.aborted) return 'Cancelled.';
		if (err instanceof ApiError) {
			if (err.status === 401) return NOT_LOGGED_IN;
			if (err.status === 412) return 'No MinGolf account linked. Link it under Account first.';
			if (err.status === 409) return 'Conflict: the slot was just booked by someone else.';
			return `Request failed: ${err.message}`;
		}
		return `Unexpected error: ${err instanceof Error ? err.message : String(err)}`;
	}
}

// ── Tool definitions ────────────────────────────────────────────────────────

function buildTools(): WebMCPTool[] {
	// Fresh client per execute: cookies come from the page origin; a no-op
	// onUnauthorized keeps tool errors out of the SPA's redirect logic.
	const api = (): ApiClient => createApiClient({ onUnauthorized: () => {} });

	/** Resolve agent-supplied club names to catalogue courses via the API. */
	const resolveFromApi = async (
		signal: AbortSignal,
		clubs: string[]
	): Promise<{ ids: string[]; names: Map<string, string>; missing: string[] } | string> => {
		const cat = await api().listCourses({}, { signal });
		const { matched, missing } = resolveCourses(cat, clubs);
		if (matched.length === 0) {
			return (
				`No courses matched: ${missing.join(', ')}. ` +
				'Use list_courses to see the catalogue, then retry with an exact club or course name.'
			);
		}
		return {
			ids: matched.map((c) => c.CourseID),
			names: new Map(matched.map((c) => [c.CourseID, `${c.CourseName} (${c.ClubName})`])),
			missing
		};
	};

	const nameLookup = (cat: Course[]) => {
		const byId = new Map(cat.map((c) => [c.CourseID, `${c.CourseName} (${c.ClubName})`]));
		return (courseId: string) => byId.get(courseId) ?? 'unknown course';
	};

	return [
		{
			name: 'list_courses',
			title: 'List golf courses',
			description:
				'Search the Golfkompis course catalogue of Swedish golf clubs. ' +
				'Returns club name, course name and course_id. No login required. ' +
				'Use course_id/club names with search_tee_times.',
			inputSchema: {
				type: 'object',
				properties: {
					search: {
						type: 'string',
						description: 'Optional substring to filter clubs, e.g. "Stockholm" or "Backa".'
					},
					only_18: { type: 'boolean', description: 'Exclude 9-hole courses. Default: false.' }
				}
			},
			annotations: { readOnlyHint: true },
			execute: async (input, { signal }) =>
				toolGuard(signal, async () => {
					const search = asString(input, 'search').trim();
					const only18 = input.only_18 === true;
					const list = search
						? await api().searchCourses({ course: search, only_18: only18 }, { signal })
						: await api().listCourses({ only_18: only18 }, { signal });
					if (list.length === 0) return `No courses matched "${search}".`;
					return list
						.slice(0, 50)
						.map(
							(c) =>
								`${c.ClubName} — ${c.CourseName}${c.IsNineHoleCourse ? ' (9 holes)' : ''} · course_id: ${c.CourseID}`
						)
						.join('\n');
				})
		},
		{
			name: 'search_tee_times',
			title: 'Search available tee times',
			description:
				'Search available golf tee times at Swedish clubs for a date. ' +
				'Returns tee times with availability, price and slot_id. ' +
				'Use club names (from list_courses) — no login required to search.',
			inputSchema: {
				type: 'object',
				properties: {
					date: { type: 'string', description: 'Date to search, YYYY-MM-DD.' },
					clubs: {
						type: 'array',
						items: { type: 'string' },
						description: 'One or more club or course names, e.g. ["Backa Säteri IF"].'
					},
					start: { type: 'string', description: 'Earliest tee time, HH:MM. Optional.' },
					stop: { type: 'string', description: 'Latest tee time, HH:MM. Optional.' },
					min_spots: {
						type: 'number',
						description: 'Minimum available spots (party size). Default: 1.'
					}
				},
				required: ['date', 'clubs']
			},
			annotations: { readOnlyHint: true },
			execute: async (input, { signal }) =>
				toolGuard(signal, async () => {
					const date = asString(input, 'date');
					if (!DATE_RE.test(date)) return 'Invalid date — use YYYY-MM-DD.';
					const clubs = asStringArray(input, 'clubs');
					if (clubs.length === 0) return 'Provide at least one club name.';
					const resolved = await resolveFromApi(signal, clubs);
					if (typeof resolved === 'string') return resolved;
					// The backend slots carry no course attribution, so search per course
					// and label the sections ourselves.
					const groups = await Promise.all(
						resolved.ids.map(async (courseId) => ({
							course: resolved.names.get(courseId) ?? 'unknown course',
							slots: await api().findSlots(
								{
									date,
									courses: [courseId],
									start: asString(input, 'start') || undefined,
									stop: asString(input, 'stop') || undefined,
									spots: asOptionalNumber(input, 'min_spots') ?? 1
								},
								{ signal }
							)
						}))
					);
					const note = resolved.missing.length
						? ` (not matched: ${resolved.missing.join(', ')})`
						: '';
					return formatSlotGroups(groups) + note;
				})
		},
		{
			name: 'get_my_bookings',
			title: 'List my bookings',
			description:
				"List the logged-in user's upcoming tee-time bookings with booking_id. Requires login.",
			inputSchema: {
				type: 'object',
				properties: {
					from: { type: 'string', description: 'Range start, YYYY-MM-DD. Optional.' },
					to: { type: 'string', description: 'Range end, YYYY-MM-DD. Optional.' }
				}
			},
			annotations: { readOnlyHint: true },
			execute: async (input, { signal }) =>
				toolGuard(signal, async () => {
					const list = await api().listBookings(
						{ from: asString(input, 'from') || undefined, to: asString(input, 'to') || undefined },
						{ signal }
					);
					return formatBookings(list);
				})
		},
		{
			name: 'book_teetime',
			title: 'Book a tee time',
			description:
				'Book a tee slot for the logged-in user by slot_id (from search_tee_times). ' +
				'Books for the account holder only — confirm the choice with the user first. Requires login.',
			inputSchema: {
				type: 'object',
				properties: {
					slot_id: { type: 'string', description: 'Slot ID from search_tee_times.' }
				},
				required: ['slot_id']
			},
			annotations: { readOnlyHint: false },
			execute: async (input, { signal }) =>
				toolGuard(signal, async () => {
					const slotId = asString(input, 'slot_id');
					if (!slotId) return 'Provide slot_id from search_tee_times.';
					await api().book({ slot_id: slotId }, { signal });
					return `Booked tee time ${slotId}. See get_my_bookings to confirm.`;
				})
		},
		{
			name: 'cancel_booking',
			title: 'Cancel my booking',
			description:
				"Cancel one of the logged-in user's upcoming bookings by booking_id (from get_my_bookings). " +
				'Confirm with the user first. Requires login.',
			inputSchema: {
				type: 'object',
				properties: {
					booking_id: { type: 'string', description: 'Booking ID from get_my_bookings.' }
				},
				required: ['booking_id']
			},
			annotations: { readOnlyHint: false },
			execute: async (input, { signal }) =>
				toolGuard(signal, async () => {
					const id = asString(input, 'booking_id');
					if (!id || id === '(unconfirmed)') return 'Provide a booking_id from get_my_bookings.';
					await api().cancelBooking(id, { signal });
					return `Cancelled booking ${id}.`;
				})
		},
		{
			name: 'add_queue_watch',
			title: 'Watch a tee time',
			description:
				'Create a tee-time watch: when a matching slot opens up, Golfkompis emails the user. ' +
				'Accepts club names (resolved like search_tee_times). Requires login.',
			inputSchema: {
				type: 'object',
				properties: {
					date: { type: 'string', description: 'Target date, YYYY-MM-DD.' },
					clubs: {
						type: 'array',
						items: { type: 'string' },
						description: 'Club or course names to watch.'
					},
					start: { type: 'string', description: 'Earliest acceptable tee time, HH:MM. Optional.' },
					stop: { type: 'string', description: 'Latest acceptable tee time, HH:MM. Optional.' },
					min_spots: { type: 'number', description: 'Minimum spots needed. Default: 1.' }
				},
				required: ['date', 'clubs']
			},
			annotations: { readOnlyHint: false },
			execute: async (input, { signal }) =>
				toolGuard(signal, async () => {
					const date = asString(input, 'date');
					if (!DATE_RE.test(date)) return 'Invalid date — use YYYY-MM-DD.';
					const clubs = asStringArray(input, 'clubs');
					if (clubs.length === 0) return 'Provide at least one club name.';
					const resolved = await resolveFromApi(signal, clubs);
					if (typeof resolved === 'string') return resolved;
					const entry = await api().createQueueEntry(
						{
							target_date: date,
							course_ids: resolved.ids,
							start_time: asString(input, 'start') || undefined,
							stop_time: asString(input, 'stop') || undefined,
							min_spots: asOptionalNumber(input, 'min_spots') ?? 1
						},
						{ signal }
					);
					return `Watching ${resolved.ids.length} course(s) on ${date} — you will get an email when a matching slot opens (watch_id: ${entry.id}).`;
				})
		},
		{
			name: 'list_queue_watches',
			title: 'List my tee-time watches',
			description:
				"List the logged-in user's active tee-time watches with watch_id and status. Requires login.",
			inputSchema: { type: 'object', properties: {} },
			annotations: { readOnlyHint: true },
			execute: async (_input, { signal }) =>
				toolGuard(signal, async () => {
					const cat = await api().listCourses({}, { signal });
					const entries = await api().listQueue(undefined, { signal });
					return formatQueue(entries, nameLookup(cat));
				})
		},
		{
			name: 'remove_queue_watch',
			title: 'Remove a tee-time watch',
			description: 'Delete a tee-time watch by watch_id (from list_queue_watches). Requires login.',
			inputSchema: {
				type: 'object',
				properties: {
					watch_id: { type: 'string', description: 'Watch ID from list_queue_watches.' }
				},
				required: ['watch_id']
			},
			annotations: { readOnlyHint: false },
			execute: async (input, { signal }) =>
				toolGuard(signal, async () => {
					const id = asString(input, 'watch_id');
					if (!id) return 'Provide watch_id from list_queue_watches.';
					await api().cancelQueueEntry(id, { signal });
					return `Removed watch ${id}.`;
				})
		}
	];
}

// ── Registration ────────────────────────────────────────────────────────────

let registered = false;

/**
 * Register Golfkompis tools on `document.modelContext` when the WebMCP API is
 * available (ChatGPT in-app browser, Chrome 149+ with WebMCP enabled).
 * Safe to call repeatedly — registration happens at most once per page.
 */
export async function registerWebMCPTools(): Promise<void> {
	if (registered) return;
	if (typeof document === 'undefined' || !('modelContext' in document)) return;
	const mc = document.modelContext;
	if (!mc) return;
	registered = true;

	for (const tool of buildTools()) {
		try {
			await mc.registerTool(tool);
		} catch (err) {
			console.warn(`[webmcp] failed to register tool "${tool.name}"`, err);
		}
	}
	console.info(`[webmcp] registered ${buildTools().length} Golfkompis tools`);
}
