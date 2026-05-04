import type { Requester } from '../client.js';
import type { QueueEntry, QueueEntryCreate, QueueEntryUpdate, ListQueueParams } from '../types.js';

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
