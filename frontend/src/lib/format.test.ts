import { describe, it, expect } from 'vitest';
import { formatSlotTime } from './format';

describe('formatSlotTime', () => {
	it('converts UTC summer-time (CEST = UTC+2) to Stockholm wall clock', () => {
		// 2026-05-10 15:30 UTC = 17:30 Stockholm (CEST)
		expect(formatSlotTime('2026-05-10T15:30:00Z')).toBe('17:30');
	});

	it('converts UTC winter-time (CET = UTC+1) to Stockholm wall clock', () => {
		// 2026-01-15 08:00 UTC = 09:00 Stockholm (CET)
		expect(formatSlotTime('2026-01-15T08:00:00Z')).toBe('09:00');
	});

	it('handles lowercase z suffix', () => {
		expect(formatSlotTime('2026-05-10T15:30:00z')).toBe('17:30');
	});

	it('respects explicit +02:00 offset', () => {
		// 08:30+02:00 is 06:30 UTC = 08:30 Stockholm (CEST)
		expect(formatSlotTime('2025-04-28T08:30:00+02:00')).toBe('08:30');
	});

	it('passes through naive ISO as local clock time (no TZ conversion)', () => {
		expect(formatSlotTime('2025-04-28T08:30:00')).toBe('08:30');
	});

	it('passes through bare HH:MM unchanged', () => {
		expect(formatSlotTime('08:30')).toBe('08:30');
	});

	it('echoes unrecognised garbage', () => {
		expect(formatSlotTime('not-a-time')).toBe('not-a-time');
	});
});
