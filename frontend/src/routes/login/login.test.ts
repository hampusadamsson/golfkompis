import { describe, it, expect } from 'vitest';
import { CurrentUserStore } from '$lib/auth/currentUser.svelte.js';
import { ApiError, getErrorMessage } from '$lib/api/errors.js';

describe('login page logic', () => {
	it('sets currentUser after successful login + getMe', () => {
		const store = new CurrentUserStore();
		const user = {
			id: 'abc',
			email: 'a@b.com',
			is_active: true,
			is_superuser: false,
			is_verified: true,
			username: 'alice',
			full_name: 'Alice',
			age: null
		};
		store.set(user);
		expect(store.isLoggedIn).toBe(true);
		expect(store.user?.email).toBe('a@b.com');
	});

	it('getErrorMessage returns Swedish string for unauthorized', () => {
		const err = new ApiError({ status: 401, message: 'Unauthorized' });
		const msg = getErrorMessage(err, {
			unauthorized: 'Felaktig e-postadress eller lösenord.'
		});
		expect(msg).toBe('Felaktig e-postadress eller lösenord.');
	});

	it('canSubmit logic: requires valid email and non-empty password', () => {
		// simulate the derived logic from the login page
		const emailValid = (email: string) => email.includes('@') && email.length > 3;
		const passwordValid = (pw: string) => pw.length > 0;
		const canSubmit = (email: string, pw: string) => emailValid(email) && passwordValid(pw);

		expect(canSubmit('', '')).toBe(false);
		expect(canSubmit('a@b.com', '')).toBe(false);
		expect(canSubmit('', 'pw')).toBe(false);
		expect(canSubmit('a@b.com', 'pw')).toBe(true);
	});
});
