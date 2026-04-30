import type { Requester } from '../client.js';
import type { Slot, Booking } from '../types.js';

export interface FindSlotsParams {
	/** Calendar date to search, e.g. `"2025-07-24"`. */
	date: string;
	/** Course UUIDs (CourseID from searchCourses). Max 50. */
	courses: string[];
	/** Earliest tee time (inclusive), e.g. `"07:30"`. */
	start?: string;
	/** Latest tee time (inclusive), e.g. `"12:00"`. */
	stop?: string;
	/** Minimum available spots required. Default: 1. */
	spots?: number;
}

export interface ListBookingsParams {
	/** Start of date range (inclusive), e.g. `"2025-07-01"`. Defaults to today. */
	from?: string;
	/** End of date range (inclusive), e.g. `"2026-07-01"`. */
	to?: string;
}

export function bookings(req: Requester) {
	return {
		/**
		 * Search available tee slots across one or more courses.
		 * Results are filtered to the requested time window and minimum party size.
		 * Slot times are in Europe/Stockholm local time.
		 * Requires authentication.
		 */
		findSlots(params: FindSlotsParams, opts?: { signal?: AbortSignal }): Promise<Slot[]> {
			return req<Slot[]>('GET', '/api/v1/booking/find', {
				query: params,
				requireAuth: true,
				signal: opts?.signal
			});
		},

		/**
		 * Book a tee slot by slot ID (UUID from findSlots).
		 * Returns void on success (HTTP 204).
		 * Throws ApiError with code `conflict` if the slot is already taken.
		 * Requires authentication.
		 */
		book(params: { slot_id: string }, opts?: { signal?: AbortSignal }): Promise<void> {
			return req<void>('POST', '/api/v1/booking', {
				body: params,
				requireAuth: true,
				signal: opts?.signal
			});
		},

		/**
		 * List the authenticated user's upcoming tee-time bookings.
		 * Requires authentication.
		 */
		listBookings(params: ListBookingsParams = {}, opts?: { signal?: AbortSignal }): Promise<Booking[]> {
			return req<Booking[]>('GET', '/api/v1/bookings', {
				query: params,
				requireAuth: true,
				signal: opts?.signal
			});
		},

		/**
		 * Cancel an upcoming booking by booking ID (`Booking.bookingInfo.bookingId`).
		 * Only cancels the requesting user's own entry — group bookings require
		 * each player to cancel separately.
		 * Lookup window is the next 10 weeks.
		 * Returns void on success (HTTP 204).
		 * Requires authentication.
		 */
		cancelBooking(bookingId: string, opts?: { signal?: AbortSignal }): Promise<void> {
			return req<void>('DELETE', `/api/v1/bookings/${encodeURIComponent(bookingId)}`, {
				requireAuth: true,
				signal: opts?.signal
			});
		}
	};
}
