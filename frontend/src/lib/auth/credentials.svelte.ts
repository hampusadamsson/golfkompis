/**
 * Reactive credentials store for MinGolf authentication.
 *
 * ⚠️  Security note: when `persist` is used, credentials are stored in
 * `localStorage` — which is readable by any JavaScript running on the page
 * (i.e. XSS-vulnerable). Use this only in trusted environments. If higher
 * security is required, store credentials server-side in an HttpOnly cookie.
 */

import type { Profile } from '$lib/api';
import { isProfile } from './guards';

const STORAGE_KEY = 'golfkompis.credentials';

interface Stored {
	username: string;
	password: string;
	profile: Profile | null;
}

function loadFromStorage(): Stored | null {
	if (typeof window === 'undefined') return null;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return null;
		const parsed = JSON.parse(raw) as unknown;
		if (
			parsed &&
			typeof parsed === 'object' &&
			'username' in parsed &&
			'password' in parsed &&
			typeof (parsed as Stored).username === 'string' &&
			typeof (parsed as Stored).password === 'string'
		) {
			const p = parsed as Record<string, unknown>;
			const profile = isProfile(p.profile) ? p.profile : null;
			return { username: p.username as string, password: p.password as string, profile };
		}
	} catch {
		// corrupted storage entry
	}
	return null;
}class CredentialsStore {
	username = $state('');
	password = $state('');
	profile = $state<Profile | null>(null);
	/** Whether credentials were loaded from / saved to localStorage. */
	isPersisted = $state(false);

	constructor() {
		const stored = loadFromStorage();
		if (stored) {
			this.username = stored.username;
			this.password = stored.password;
			this.profile = stored.profile;
			this.isPersisted = true;
		}
	}

	/** True when both username and password are non-empty. */
	get isSet(): boolean {
		return this.username !== '' && this.password !== '';
	}

	/** The credentials as an `ApiCredentials` object, or `undefined` if not set. */
	get value(): { username: string; password: string } | undefined {
		if (!this.isSet) return undefined;
		return { username: this.username, password: this.password };
	}

	/**
	 * Set the credentials.
	 * @param persist - If true, save to localStorage so they survive a page reload.
	 */
	set(username: string, password: string, profile: Profile | null, persist = false): void {
		this.username = username;
		this.password = password;
		this.profile = profile;
		this.isPersisted = persist;

		if (typeof window === 'undefined') return;
		if (persist) {
			localStorage.setItem(STORAGE_KEY, JSON.stringify({ username, password, profile }));
		} else {
			localStorage.removeItem(STORAGE_KEY);
		}
	}

	/** Clear credentials from memory and localStorage. */
	clear(): void {
		this.username = '';
		this.password = '';
		this.profile = null;
		this.isPersisted = false;
		if (typeof window !== 'undefined') {
			localStorage.removeItem(STORAGE_KEY);
		}
	}
}

export const credentials = new CredentialsStore();
