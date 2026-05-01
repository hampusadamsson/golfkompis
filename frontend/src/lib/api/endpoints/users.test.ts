import { describe, it, expect, vi } from 'vitest';
import { users } from './users.js';

describe('users endpoint', () => {
	it('register calls POST /auth/register', async () => {
		const req = vi.fn().mockResolvedValue({
			id: '123',
			email: 'a@b.com',
			is_active: true,
			is_superuser: false,
			is_verified: false,
			username: null,
			full_name: null,
			age: null
		});
		const client = users(req);
		await client.register({
			email: 'a@b.com',
			password: 'pw',
			username: null,
			full_name: null,
			age: null
		});
		expect(req).toHaveBeenCalledWith(
			'POST',
			'/auth/register',
			expect.objectContaining({ body: expect.objectContaining({ email: 'a@b.com' }) })
		);
	});

	it('getMe calls GET /users/me', async () => {
		const req = vi.fn().mockResolvedValue({
			id: '123',
			email: 'a@b.com',
			is_active: true,
			is_superuser: false,
			is_verified: false,
			username: null,
			full_name: null,
			age: null
		});
		const client = users(req);
		await client.getMe();
		expect(req).toHaveBeenCalledWith('GET', '/users/me', expect.anything());
	});
});
