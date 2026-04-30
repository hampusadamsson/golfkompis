// Public API surface for the golfkompis API client.
//
// Usage:
//   import { createApiClient, ApiError } from '$lib/api';
//   import type { Slot, Booking, Profile, Course, Friend } from '$lib/api';

export { createApiClient } from './client.js';
export type { ApiClient, ApiConfig, ApiCredentials } from './client.js';

export { ApiError, getErrorMessage } from './errors.js';
export type { ApiErrorCode } from './errors.js';

export type {
	HealthResponse,
	Course,
	Slot,
	SlotPrice,
	SlotAvailability,
	Booking,
	BookingInfo,
	BookingPlayer,
	BookingRequest,
	Profile,
	MemberClub,
	Friend,
	FriendOverview,
	FriendTee,
	ValidationErrorDetail,
	HTTPValidationError
} from './types.js';

export type { FindSlotsParams, ListBookingsParams } from './endpoints/bookings.js';
export type { SearchCoursesParams, ListCoursesParams } from './endpoints/courses.js';
export type { HistoryParams } from './endpoints/history.js';
