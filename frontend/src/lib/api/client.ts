import { ApiError } from './errors.js';
import { meta } from './endpoints/meta.js';
import { courses } from './endpoints/courses.js';
import { bookings } from './endpoints/bookings.js';
import { history } from './endpoints/history.js';
import { profile } from './endpoints/profile.js';
import { friends } from './endpoints/friends.js';
import { users } from './endpoints/users.js';
import { queue } from './endpoints/queue.js';

// ── Global 401 interceptor ───────────────────────────────────────────────────
// Register once from +layout.svelte to handle session expiry across the app.

let _globalOnUnauthorized: (() => void) | undefined;

/**
 * Register a global handler called whenever any API request returns HTTP 401.
 * Typically used to clear auth state and redirect to /login.
 * Call once from root layout.
 */
export function setGlobalOnUnauthorized(handler: () => void): void {
	_globalOnUnauthorized = handler;
}

export interface ApiConfig {
	/**
	 * Base URL of the golfkompis API.
	 * @default 'http://localhost:8000'
	 */
	baseUrl?: string;
	/**
	 * Custom fetch implementation. Pass `fetch` from a SvelteKit `load()` context
	 * for SSR-compatible requests.
	 * @default globalThis.fetch
	 */
	fetch?: typeof globalThis.fetch;
	/**
	 * Called when a request returns HTTP 401 (session expired / not authenticated).
	 * Use this to clear auth state and redirect to /login.
	 */
	onUnauthorized?: () => void;
}

// Internal option shape passed from endpoint functions into request()
interface RequestOptions {
	query?: object;
	body?: unknown;
	rawBody?: string;
	contentType?: string;
	signal?: AbortSignal;
}

/** Internal type for the request helper bound to a specific client config. */
export type Requester = <T>(
	method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
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

function createRequester(config: Required<Pick<ApiConfig, 'baseUrl' | 'fetch'>> & Pick<ApiConfig, 'onUnauthorized'>): Requester {
	return async function request<T>(
		method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
		path: string,
		opts: RequestOptions = {}
	): Promise<T> {
		const { query, body, signal } = opts;

		// Build URL
		const qs = query ? buildQuery(query) : '';
		const url = `${config.baseUrl}${path}${qs}`;

		// Build headers
		const headers: Record<string, string> = {
			Accept: 'application/json'
		};
		if (opts.contentType) {
			headers['Content-Type'] = opts.contentType;
		} else if (body !== undefined) {
			headers['Content-Type'] = 'application/json';
		}
		let res: Response;
		try {
			res = await config.fetch(url, {
				method,
				headers,
				body: opts.rawBody ?? (body !== undefined ? JSON.stringify(body) : undefined),
				signal,
				credentials: 'include'
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

		// Global 401 hook — session expired or not authenticated
		if (res.status === 401 && config.onUnauthorized) {
			config.onUnauthorized();
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
type UsersClient = ReturnType<typeof users>;
type QueueClient = ReturnType<typeof queue>;

export type ApiClient = MetaClient &
	CoursesClient &
	BookingsClient &
	HistoryClient &
	ProfileClient &
	FriendsClient &
	UsersClient &
	QueueClient;

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
 * // SSR-friendly inside a SvelteKit load()
 * export const load = async ({ fetch }) => {
 *   const api = createApiClient({ fetch });
 *   return { courses: await api.searchCourses({ course: 'Stockholm' }) };
 * };
 * ```
 */
export function createApiClient(config: ApiConfig = {}): ApiClient {
	const resolved = {
		baseUrl: config.baseUrl ?? '',
		fetch: config.fetch ?? globalThis.fetch,
		onUnauthorized: config.onUnauthorized ?? _globalOnUnauthorized,
	};

	const req = createRequester(resolved);

	return {
		...meta(req),
		...courses(req),
		...bookings(req),
		...history(req),
		...profile(req),
		...friends(req),
		...users(req),
		...queue(req)
	};
}
