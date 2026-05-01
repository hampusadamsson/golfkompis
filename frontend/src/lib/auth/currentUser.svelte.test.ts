import { describe, it, expect } from 'vitest';
import { CurrentUserStore } from './currentUser.svelte.js';

describe('CurrentUserStore', () => {
	it('starts with null user and false loading', () => {
		const store = new CurrentUserStore();
		expect(store.user).toBeNull();
		expect(store.loading).toBe(false);
	});

	it('set() updates user', () => {
		const store = new CurrentUserStore();
		const user = {
			id: '1',
			email: 'a@b.com',
			is_active: true,
			is_superuser: false,
			is_verified: true,
			username: 'alice',
			full_name: 'Alice',
			mingolf_username: null,
			mingolf_password: null
		};
		store.set(user);
		expect(store.user).toEqual(user);
		expect(store.isLoggedIn).toBe(true);
	});

	it('clear() resets user', () => {
		const store = new CurrentUserStore();
		store.set({
			id: '1',
			email: 'a@b.com',
			is_active: true,
			is_superuser: false,
			is_verified: true,
			username: null,
			full_name: null,
			mingolf_username: null,
			mingolf_password: null
		});
		store.clear();
		expect(store.user).toBeNull();
		expect(store.isLoggedIn).toBe(false);
	});
});
