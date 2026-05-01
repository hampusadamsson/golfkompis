import { describe, it, expect, vi } from 'vitest';
import { MinGolfProfileStore } from './mingolfProfile.svelte.js';
import type { ApiClient } from '$lib/api/client';
import type { Profile } from '$lib/api';

const fakeProfile = {
	firstName: 'Anna',
	lastName: 'Svensson',
	email: 'anna@golf.se',
	hcp: 12.0,
	clubMemberships: [],
} as unknown as Profile;

function makeApi(override: Partial<ApiClient> = {}): ApiClient {
	return {
		getProfile: vi.fn().mockResolvedValue(fakeProfile),
		...override,
	} as unknown as ApiClient;
}

describe('MinGolfProfileStore', () => {
	it('load() sets profile on success', async () => {
		const store = new MinGolfProfileStore();
		await store.load(makeApi());
		expect(store.profile).toEqual(fakeProfile);
		expect(store.loading).toBe(false);
		expect(store.error).toBeNull();
	});

	it('load() sets error on failure', async () => {
		const api = makeApi({
			getProfile: vi.fn().mockRejectedValue(new Error('network error')),
		});
		const store = new MinGolfProfileStore();
		await store.load(api);
		expect(store.profile).toBeNull();
		expect(store.error).toBeTruthy();
		expect(store.loading).toBe(false);
	});

	it('clear() resets all state', async () => {
		const store = new MinGolfProfileStore();
		await store.load(makeApi());
		expect(store.profile).not.toBeNull();
		store.clear();
		expect(store.profile).toBeNull();
		expect(store.error).toBeNull();
	});

	it('isLinked returns true when profile is set', async () => {
		const store = new MinGolfProfileStore();
		expect(store.isLinked).toBe(false);
		await store.load(makeApi());
		expect(store.isLinked).toBe(true);
	});
});
