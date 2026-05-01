import type { AppUser } from '$lib/api/endpoints/users.js';

export class CurrentUserStore {
	user = $state<AppUser | null>(null);
	loading = $state(false);

	get isLoggedIn(): boolean {
		return this.user !== null;
	}

	set(user: AppUser): void {
		this.user = user;
	}

	clear(): void {
		this.user = null;
	}
}

export const currentUser = new CurrentUserStore();
