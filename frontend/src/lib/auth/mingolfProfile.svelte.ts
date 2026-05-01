import type { Profile } from '$lib/api';
import type { ApiClient } from '$lib/api/client';
import { getErrorMessage } from '$lib/api/errors';

export class MinGolfProfileStore {
	profile = $state<Profile | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);

	get isLinked(): boolean {
		return this.profile !== null;
	}

	async load(api: ApiClient): Promise<void> {
		this.loading = true;
		this.error = null;
		try {
			this.profile = await api.getProfile();
		} catch (e) {
			this.error = getErrorMessage(e);
			this.profile = null;
		} finally {
			this.loading = false;
		}
	}

	clear(): void {
		this.profile = null;
		this.error = null;
		this.loading = false;
	}
}

export const mingolfProfile = new MinGolfProfileStore();
