import type { Requester } from '../client.js';
import type { HealthResponse } from '../types.js';

export function meta(req: Requester) {
	return {
		/**
		 * Liveness probe. No authentication required.
		 * Returns `{ status: "ok" }` while the service is running.
		 */
		health(opts?: { signal?: AbortSignal }): Promise<HealthResponse> {
			return req<HealthResponse>('GET', '/health', { signal: opts?.signal });
		}
	};
}
