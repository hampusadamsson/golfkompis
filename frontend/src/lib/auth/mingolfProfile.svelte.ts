import type { Profile } from '$lib/api';
import type { ApiClient } from '$lib/api/client';
import { getErrorMessage } from '$lib/api/errors';

export class MinGolfProfileStore {
	profile = $state<Profile | null>(null);
	loading = $state(false);
	error = $state<string | null>(null);
	#seq = 0;

	get isLinked(): boolean {
		return this.profile !== null;
	}

	async load(api: ApiClient): Promise<void> {
		const seq = ++this.#seq;
		this.loading = true;
		this.error = null;
		try {
			const result = await api.getProfile();
			if (seq !== this.#seq) return; // stale response — a newer load() superseded this one
			this.profile = result;
		} catch (e) {
			if (seq !== this.#seq) return;
			this.error = getErrorMessage(e);
			this.profile = null;
		} finally {
			if (seq === this.#seq) this.loading = false;
		}
	}

	clear(): void {
		++this.#seq; // invalidate any in-flight load()
		this.profile = null;
		this.error = null;
		this.loading = false;
	}
}

export const mingolfProfile = new MinGolfProfileStore();
