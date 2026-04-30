import type { Profile } from '$lib/api/types';

/**
 * Type guard for the Profile shape stored in localStorage.
 * Validates only the fields that are reliably present; the rest are
 * checked by TypeScript at compile time once the guard passes.
 */
export function isProfile(x: unknown): x is Profile {
	if (!x || typeof x !== 'object') return false;
	const p = x as Record<string, unknown>;
	return (
		typeof p.sessionId === 'string' &&
		typeof p.personId === 'string' &&
		typeof p.firstName === 'string' &&
		typeof p.lastName === 'string' &&
		typeof p.golfId === 'string'
	);
}
