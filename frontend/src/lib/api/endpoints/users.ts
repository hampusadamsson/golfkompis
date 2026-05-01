import type { Requester } from '../client.js';

export interface AppUser {
	id: string;
	email: string;
	is_active: boolean;
	is_superuser: boolean;
	is_verified: boolean;
	username: string | null;
	full_name: string | null;
	age: number | null;
}

export interface UserCreate {
	email: string;
	password: string;
	username: string | null;
	full_name: string | null;
	age: number | null;
}

export interface UserUpdate {
	username?: string | null;
	full_name?: string | null;
	age?: number | null;
}

export function users(req: Requester) {
	return {
		register(body: UserCreate): Promise<AppUser> {
			return req('POST', '/auth/register', { body });
		},
		login(creds: { username: string; password: string }): Promise<void> {
			const rawBody = new URLSearchParams(creds).toString();
			return req('POST', '/auth/login', {
				rawBody,
				contentType: 'application/x-www-form-urlencoded'
			});
		},
		logout(): Promise<void> {
			return req('POST', '/auth/logout', {});
		},
		getMe(): Promise<AppUser> {
			return req('GET', '/users/me', {});
		},
		patchMe(body: UserUpdate): Promise<AppUser> {
			return req('PATCH', '/users/me', { body });
		},
		deleteMe(): Promise<void> {
			return req('DELETE', '/users/me', {});
		},
		forgotPassword(body: { email: string }): Promise<void> {
			return req('POST', '/auth/forgot-password', { body });
		},
		resetPassword(body: { token: string; password: string }): Promise<void> {
			return req('POST', '/auth/reset-password', { body });
		},
		requestVerify(body: { email: string }): Promise<void> {
			return req('POST', '/auth/request-verify-token', { body });
		},
		verifyEmail(body: { token: string }): Promise<AppUser> {
			return req('POST', '/auth/verify', { body });
		}
	};
}
