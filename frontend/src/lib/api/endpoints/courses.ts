import type { Requester } from '../client.js';
import type { Course } from '../types.js';

export interface SearchCoursesParams {
	/** Substring to match against club name (minimum 2 characters). */
	course: string;
	/** If true, exclude 9-hole courses. Default: false. */
	only_18?: boolean;
	/** Maximum results to return (1–500). Default: 50. */
	limit?: number;
}

export interface ListCoursesParams {
	/** If true, exclude 9-hole courses. Default: false. */
	only_18?: boolean;
}

export function courses(req: Requester) {
	return {
		/**
		 * Search the bundled course catalogue by club name.
		 * Case-insensitive substring match. No authentication required.
		 */
		searchCourses(params: SearchCoursesParams, opts?: { signal?: AbortSignal }): Promise<Course[]> {
			return req<Course[]>('GET', '/api/v1/course/search', {
				query: params,
				signal: opts?.signal
			});
		},

		/**
		 * Return the full bundled course catalogue.
		 * No authentication required.
		 */
		listCourses(params: ListCoursesParams = {}, opts?: { signal?: AbortSignal }): Promise<Course[]> {
			return req<Course[]>('GET', '/api/v1/course/list', {
				query: params,
				signal: opts?.signal
			});
		}
	};
}
