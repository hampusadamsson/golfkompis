import { ApiError } from './errors.js';
import { meta } from './endpoints/meta.js';
import { courses } from './endpoints/courses.js';
import { bookings } from './endpoints/bookings.js';
import { history } from './endpoints/history.js';
import { profile } from './endpoints/profile.js';
import { friends } from './endpoints/friends.js';

export interface ApiCredentials {
	username: string;
	password: string;
}

export interface ApiConfig {
	/**
	 * Base URL of the golfkompis API.
	 * @default 'http://localhost:8000'
	 */
	baseUrl?: string;
	/**
	 * MinGolf credentials. Required for authenticated endpoints.
	 * The API validates credentials upstream on every request — no session is cached.
	 */
	credentials?: ApiCredentials;
	/**
	 * Custom fetch implementation. Pass `fetch` from a SvelteKit `load()` context
	 * for SSR-compatible requests.
	 * @default globalThis.fetch
	 */
	fetch?: typeof globalThis.fetch;
}

// Internal option shape passed from endpoint functions into request()
interface RequestOptions {
	query?: object;
	body?: unknown;
	requireAuth?: boolean;
	signal?: AbortSignal;
}

/** Internal type for the request helper bound to a specific client config. */
export type Requester = <T>(
	method: 'GET' | 'POST' | 'DELETE',
	path: string,
	opts?: RequestOptions
) => Promise<T>;

function buildQuery(params: object): string {
	const qs = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value === undefined || value === null) continue;
		if (Array.isArray(value)) {
			for (const v of value) qs.append(key, String(v));
		} else {
			qs.set(key, String(value));
		}
	}
	const str = qs.toString();
	return str ? `?${str}` : '';
}

function createRequester(config: Required<ApiConfig>): Requester {
	return async function request<T>(
		method: 'GET' | 'POST' | 'DELETE',
		path: string,
		opts: RequestOptions = {}
	): Promise<T> {
		const { query, body, requireAuth = false, signal } = opts;

		// Auth check
		if (requireAuth && (!config.credentials?.username || !config.credentials?.password)) {
			throw new ApiError({
				status: 401,
				code: 'unauthorized',
				message: 'No credentials configured. Pass credentials to createApiClient().'
			});
		}

		// Build URL
		const qs = query ? buildQuery(query) : '';
		const url = `${config.baseUrl}${path}${qs}`;

		// Build headers
		const headers: Record<string, string> = {
			Accept: 'application/json'
		};
		if (requireAuth) {
			headers['X-Mingolf-Username'] = config.credentials.username;
			headers['X-Mingolf-Password'] = config.credentials.password;
		}
		if (body !== undefined) {
			headers['Content-Type'] = 'application/json';
		}

		// Fetch
		let res: Response;
		try {
			res = await config.fetch(url, {
				method,
				headers,
				body: body !== undefined ? JSON.stringify(body) : undefined,
				signal
			});
		} catch (err) {
			throw ApiError.network(err);
		}

		// Success
		if (res.status === 204) {
			return undefined as T;
		}
		if (res.ok) {
			return (await res.json()) as T;
		}

		// Error
		throw await ApiError.fromResponse(res);
	};
}

// ── Public client type ──────────────────────────────────────────────────────

type MetaClient = ReturnType<typeof meta>;
type CoursesClient = ReturnType<typeof courses>;
type BookingsClient = ReturnType<typeof bookings>;
type HistoryClient = ReturnType<typeof history>;
type ProfileClient = ReturnType<typeof profile>;
type FriendsClient = ReturnType<typeof friends>;

export type ApiClient = MetaClient &
	CoursesClient &
	BookingsClient &
	HistoryClient &
	ProfileClient &
	FriendsClient;

// ── Factory ─────────────────────────────────────────────────────────────────

/**
 * Create a bound API client for the golfkompis backend.
 *
 * @example
 * ```ts
 * // Anonymous — only health() and searchCourses() work
 * const api = createApiClient();
 * await api.health();
 * const courses = await api.searchCourses({ course: 'Botkyrka', only_18: true });
 *
 * // Authenticated
 * const api = createApiClient({
 *   baseUrl: 'http://localhost:8000',
 *   credentials: { username, password },
 * });
 * const profile = await api.getProfile();
 * const slots = await api.findSlots({
 *   date: '2025-07-24',
 *   courses: ['98369cac-d4bb-4671-931f-db10201ba1a5'],
 *   start: '07:30',
 *   stop: '12:00',
 *   spots: 4,
 * });
 * await api.book({ slot_id: slots[0].id });
 *
 * // SSR-friendly inside a SvelteKit load()
 * export const load = async ({ fetch }) => {
 *   const api = createApiClient({ fetch });
 *   return { courses: await api.searchCourses({ course: 'Stockholm' }) };
 * };
 * ```
 */
export function createApiClient(config: ApiConfig = {}): ApiClient {
	const resolved: Required<ApiConfig> = {
		baseUrl: config.baseUrl ?? '',
		credentials: config.credentials ?? { username: '', password: '' },
		fetch: config.fetch ?? globalThis.fetch
	};

	const req = createRequester(resolved);

	return {
		...meta(req),
		...courses(req),
		...bookings(req),
		...history(req),
		...profile(req),
		...friends(req)
	};
}
