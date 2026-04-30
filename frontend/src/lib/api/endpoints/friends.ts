import type { Requester } from '../client.js';
import type { FriendOverview } from '../types.js';

export function friends(req: Requester) {
	return {
		/**
		 * Fetch the authenticated user's friend overview.
		 * Returns both the user's own friend list (`friends`) and the reverse list
		 * (`reversedFriends` — users who have added the authenticated user as a friend).
		 * Requires authentication.
		 */
		getFriends(opts?: { signal?: AbortSignal }): Promise<FriendOverview> {
			return req<FriendOverview>('GET', '/api/v1/friends', {
				requireAuth: true,
				signal: opts?.signal
			});
		}
	};
}
