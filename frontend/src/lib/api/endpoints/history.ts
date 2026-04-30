import type { Requester } from '../client.js';
import type { Booking } from '../types.js';

export interface HistoryParams {
	/** Start of date range (inclusive), e.g. `"2025-01-01"`. Defaults to today − default_range_weeks. */
	from?: string;
	/** End of date range (inclusive), e.g. `"2025-12-31"`. Defaults to today. */
	to?: string;
}

export function history(req: Requester) {
	return {
		/**
		 * List the authenticated user's played rounds.
		 * Requires authentication.
		 */
		getHistory(params: HistoryParams = {}, opts?: { signal?: AbortSignal }): Promise<Booking[]> {
			return req<Booking[]>('GET', '/api/v1/history', {
				query: params,
				requireAuth: true,
				signal: opts?.signal
			});
		}
	};
}
