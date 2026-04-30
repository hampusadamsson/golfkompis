// ---------------------------------------------------------------------------
// Schema types — mirrored verbatim from the OpenAPI spec (casing preserved).
// ---------------------------------------------------------------------------

export interface HealthResponse {
	status: string;
}

// ── Courses ────────────────────────────────────────────────────────────────

export interface Course {
	ClubID: string;
	ClubName: string;
	CourseID: string;
	CourseName: string;
	IsNineHoleCourse: boolean;
}

// ── Slots ──────────────────────────────────────────────────────────────────

export interface SlotPrice {
	greenfee: number | null;
}

export interface SlotAvailability {
	bookable: boolean;
	maxNumberOfSlotBookings: number;
	numbersOfSlotBookings: number;
	numberOfBlockedRows: number;
	numberOfNineHoleSlotBookings: number;
	availableSlots: number;
}

export interface Slot {
	id: string;
	time: string;
	price: SlotPrice;
	flexColor: string;
	nineHoleBookingAavailable: boolean;
	isLocked: boolean;
	availablity: SlotAvailability;
	playersInfo: string[];
	reservationIds: string[];
	startProhibitionIds: string[];
	maximumHcpPerSlot: string | null;
}

// ── Bookings ───────────────────────────────────────────────────────────────

export interface BookingPlayer {
	hcp: string;
	gender: string;
	personId: string | null;
	name: string | null;
}

export interface BookingInfo {
	bookingId: string;
	players: BookingPlayer[];
	hcpResult: string | null;
	points: number | null;
}

export interface Booking {
	clubId: string;
	clubName: string;
	courseId: string;
	courseName: string;
	slotId: string;
	slotTime: string;
	slotTimeAsDate: string;
	bookingInfo: BookingInfo | null;
	roundType: string;
}

export interface BookingRequest {
	slot_id: string;
}

// ── Profile ────────────────────────────────────────────────────────────────

export interface MemberClub {
	isHomeClub: boolean;
	id: string;
	name: string;
}

export interface Profile {
	sessionId: string;
	personId: string;
	firstName: string;
	lastName: string;
	golfId: string;
	homeClubId: string | null;
	homeClubName: string | null;
	districtName: string | null;
	favouriteClubId: string | null;
	representationClubName: string | null;
	representationClubShort: string | null;
	gender: string;
	birthDate: string;
	age: number;
	hcp: string;
	allowedToBook: boolean;
	allowedToBookWithNoCharge: boolean;
	allowedToCompetitionSignUp: boolean;
	allowedToCompetitionSignUpNoCharge: boolean;
	allowedToPay: boolean;
	emailAddress: string | null;
	hasActiveMembership: boolean;
	loggedInToMinGolfThisYear: boolean;
	minors: unknown[];
	memberClubs: MemberClub[];
	caregiverPersonId: string | null;
	caregiverGolfId: string | null;
	isMinor: boolean;
	isMinorWithoutCaregiver: boolean;
	imageUrl: string | null;
	isDefaultSupport: boolean;
	isFederationSuspended: boolean;
	isFederationSuspendedCompetition: boolean;
	isMinorNotLoggedInAsCaregiver: boolean;
	capped: boolean;
	softCap: string | null;
	hardCap: string | null;
	lowestHcp: string | null;
	hcpCard: string | null;
	isSgfJunior: boolean;
	isMemberOfTeenTourClub: boolean;
	hasPaidTeenTourYearlyFee: boolean;
	mustChangePassword: boolean;
	isLoggedInWithFreja: boolean;
	showPersonInfoView: boolean;
	isForeign: boolean;
	country: string | null;
}

// ── Friends ────────────────────────────────────────────────────────────────

export interface FriendTee {
	saveAsDefault: boolean;
}

export interface Friend {
	personId: string;
	golfId: string;
	firstName: string;
	lastName: string;
	fullName: string;
	hcp: string;
	age: number;
	gender: string;
	isBooker: boolean;
	homeClub: string | null;
	isGuest: boolean;
	tee: FriendTee;
	country: string | null;
	imageUrl: string | null;
}

export interface FriendOverview {
	friends: Friend[];
	reversedFriends: Friend[];
}

// ── Errors ─────────────────────────────────────────────────────────────────

export interface ValidationErrorDetail {
	loc: (string | number)[];
	msg: string;
	type: string;
	input: unknown;
	ctx?: Record<string, unknown>;
}

export interface HTTPValidationError {
	detail: ValidationErrorDetail[];
}
