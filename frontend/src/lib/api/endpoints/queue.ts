import type { Requester } from '../client.js';
import type { Slot } from '../types.js';

export type QueueStatus = 'active' | 'matched' | 'expired' | 'cancelled';

export interface QueueEntry {
	id: string;
	target_date: string;
	start_time: string | null;
	stop_time: string | null;
	min_spots: number;
	course_ids: string[];
	status: QueueStatus;
	created_at: string;
	last_checked_at: string | null;
	check_count: number;
	resolved_at: string | null;
	matched_slots: Slot[] | null;
}

export interface QueueEntryCreate {
	target_date: string;
	start_time?: string;
	stop_time?: string;
	min_spots?: number;
	course_ids: string[];
}

export interface QueueEntryUpdate {
	start_time?: string | null;
	stop_time?: string | null;
	min_spots?: number;
	course_ids?: string[];
}

export interface ListQueueParams {
	status?: QueueStatus;
}

export function queue(req: Requester) {
	return {
		listQueue(params?: ListQueueParams, opts?: { signal?: AbortSignal }): Promise<QueueEntry[]> {
			return req<QueueEntry[]>('GET', '/api/v1/queue', {
				query: params,
				signal: opts?.signal
			});
		},

		createQueueEntry(body: QueueEntryCreate, opts?: { signal?: AbortSignal }): Promise<QueueEntry> {
			return req<QueueEntry>('POST', '/api/v1/queue', {
				body,
				signal: opts?.signal
			});
		},

		getQueueEntry(id: string, opts?: { signal?: AbortSignal }): Promise<QueueEntry> {
			return req<QueueEntry>('GET', `/api/v1/queue/${encodeURIComponent(id)}`, {
				signal: opts?.signal
			});
		},

		updateQueueEntry(
			id: string,
			body: QueueEntryUpdate,
			opts?: { signal?: AbortSignal }
		): Promise<QueueEntry> {
			return req<QueueEntry>('PATCH', `/api/v1/queue/${encodeURIComponent(id)}`, {
				body,
				signal: opts?.signal
			});
		},

		cancelQueueEntry(id: string, opts?: { signal?: AbortSignal }): Promise<void> {
			return req<void>('DELETE', `/api/v1/queue/${encodeURIComponent(id)}`, {
				signal: opts?.signal
			});
		}
	};
}
