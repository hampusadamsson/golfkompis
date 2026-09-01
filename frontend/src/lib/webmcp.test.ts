import { describe, expect, it } from 'vitest';
import {
	formatBookings,
	formatQueue,
	formatSlotGroups,
	normalizeName,
	resolveCourses
} from './webmcp';
import type { Booking, Course, QueueEntry, Slot } from './api/types';

const catalogue: Course[] = [
	{
		ClubID: 'c1',
		ClubName: 'Backa Säteri IF',
		CourseID: 'k1',
		CourseName: 'Backa Säteri Golf',
		IsNineHoleCourse: true
	},
	{
		ClubID: 'c2',
		ClubName: 'Bro Hof Slott GC',
		CourseID: 'k2',
		CourseName: 'Castle Course',
		IsNineHoleCourse: false
	},
	{
		ClubID: 'c3',
		ClubName: 'Ullna GC',
		CourseID: 'k3',
		CourseName: 'Ullna Sjöbana',
		IsNineHoleCourse: false
	}
];

const slot = (time: string, spots: number): Slot => ({
	id: `slot-${time}`,
	time: `2026-09-15T${time}:00Z`,
	price: { greenfee: 450 },
	flexColor: 'green',
	nineHoleBookingAavailable: false,
	isLocked: false,
	availablity: {
		bookable: true,
		maxNumberOfSlotBookings: 4,
		numbersOfSlotBookings: 4 - spots,
		numberOfBlockedRows: 0,
		numberOfNineHoleSlotBookings: 0,
		availableSlots: spots
	},
	playersInfo: [],
	reservationIds: [],
	startProhibitionIds: [],
	maximumHcpPerSlot: null
});

describe('normalizeName', () => {
	it('lowercases, transliterates å/ä/ö and collapses punctuation', () => {
		expect(normalizeName('Backa Säteri IF')).toBe('backa sateri if');
		expect(normalizeName('Sjöö-Borg, GK')).toBe('sjoo borg gk');
	});
});

describe('resolveCourses', () => {
	it('matches substrings of club and course names, diacritics-insensitively', () => {
		const { matched, missing } = resolveCourses(catalogue, ['backa sateri', 'Bro Hof', 'ullna']);
		expect(matched.map((c) => c.CourseID)).toEqual(['k1', 'k2', 'k3']);
		expect(missing).toEqual([]);
	});

	it('prefers exact course-name matches over club-name matches', () => {
		const { matched } = resolveCourses(catalogue, ['Castle Course']);
		expect(matched).toHaveLength(1);
		expect(matched[0].CourseID).toBe('k2');
	});

	it('reports unmatched queries', () => {
		const { matched, missing } = resolveCourses(catalogue, ['Riksens Herrar']);
		expect(matched).toHaveLength(0);
		expect(missing).toEqual(['Riksens Herrar']);
	});

	it('deduplicates multiple queries hitting the same course', () => {
		const { matched } = resolveCourses(catalogue, ['Bro Hof', 'bro hof slott']);
		expect(matched).toHaveLength(1);
	});
});

describe('formatSlotGroups', () => {
	it('groups slots per course with times, spots and slot ids', () => {
		const out = formatSlotGroups([
			{ course: 'Backa Säteri Golf (Backa Säteri IF)', slots: [slot('05:00', 4)] }
		]);
		expect(out).toContain('Backa Säteri Golf (Backa Säteri IF):');
		expect(out).toContain('05:00 · 4 spots — 450 SEK · slot_id: slot-05:00');
	});

	it('returns a clear message when nothing matched', () => {
		expect(formatSlotGroups([{ course: 'X', slots: [] }])).toContain('No available tee times');
	});
});

describe('formatBookings', () => {
	it('lists bookings with booking ids', () => {
		const b: Booking[] = [
			{
				clubId: 'c1',
				clubName: 'Backa Säteri IF',
				courseId: 'k1',
				courseName: 'Backa Säteri Golf',
				slotId: 's1',
				slotTime: '2026-09-20T06:30:00Z',
				slotTimeAsDate: '2026-09-20',
				bookingInfo: {
					bookingId: 'b-123',
					players: [],
					hcpResult: null,
					points: null
				},
				roundType: '18'
			}
		];
		const out = formatBookings(b);
		expect(out).toContain('2026-09-20 06:30');
		expect(out).toContain('booking_id: b-123');
	});
});

describe('formatQueue', () => {
	it('lists watches with ids and status', () => {
		const e: QueueEntry[] = [
			{
				id: 'q1',
				target_date: '2026-09-21',
				start_time: '07:00',
				stop_time: '10:00',
				min_spots: 2,
				course_ids: ['k2'],
				status: 'active',
				created_at: '2026-09-01T00:00:00Z',
				last_checked_at: null,
				check_count: 0,
				resolved_at: null,
				matched_slots: null
			}
		];
		const out = formatQueue(e, (id) => (id === 'k2' ? 'Castle Course' : id));
		expect(out).toContain('2026-09-21 · Castle Course');
		expect(out).toContain('watch_id: q1');
	});
});
