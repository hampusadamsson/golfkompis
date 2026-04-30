import type { Requester } from '../client.js';
import type { Profile } from '../types.js';

export function profile(req: Requester) {
	return {
		/**
		 * Fetch the authenticated user's MinGolf profile.
		 * Includes HCP, membership clubs, and booking permissions.
		 * Requires authentication.
		 */
		getProfile(opts?: { signal?: AbortSignal }): Promise<Profile> {
			return req<Profile>('GET', '/api/v1/profile', {
				requireAuth: true,
				signal: opts?.signal
			});
		}
	};
}
