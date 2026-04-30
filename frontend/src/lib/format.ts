/**
 * Shared date/time formatting utilities.
 *
 * All slot times are displayed in Europe/Stockholm regardless of the user's
 * local timezone, matching the booking system's semantics.
 */

const TZ = 'Europe/Stockholm';

export const dateFmt = new Intl.DateTimeFormat('sv-SE', {
	dateStyle: 'medium',
	timeZone: TZ
});

export const dateLongFmt = new Intl.DateTimeFormat('sv-SE', {
	dateStyle: 'long',
	timeZone: TZ
});

export const timeFmt = new Intl.DateTimeFormat('sv-SE', {
	hour: '2-digit',
	minute: '2-digit',
	hour12: false,
	timeZone: TZ
});

/** Returns today's date as YYYY-MM-DD in the Stockholm timezone. */
export function todayInTz(): string {
	return new Intl.DateTimeFormat('sv-SE', { timeZone: TZ }).format(new Date());
}

/** Format an ISO datetime string as a medium date (e.g. "28 apr. 2025"). */
export function formatDate(iso: string): string {
	try {
		return dateFmt.format(new Date(iso));
	} catch {
		return iso;
	}
}

/** Format an ISO datetime string as a long date (e.g. "28 april 2025"). */
export function formatDateLong(iso: string): string {
	try {
		return dateLongFmt.format(new Date(iso));
	} catch {
		return iso;
	}
}

/**
 * Extract HH:MM from a slot time string.
 * Accepts full ISO datetimes ("2025-04-28T08:30:00") or bare times ("08:30").
 * Falls back to full Intl formatting for unrecognised formats.
 */
export function formatSlotTime(slotTime: string): string {
	const m = /T?(\d{2}:\d{2})/.exec(slotTime);
	if (m?.[1]) return m[1];
	try {
		return timeFmt.format(new Date(slotTime));
	} catch {
		return slotTime;
	}
}

/**
 * Return a CSS color value if the string is a safe named color or hex code,
 * otherwise return undefined.
 */
export function flexColorStyle(color: string | null | undefined): string | undefined {
	if (!color) return undefined;
	if (/^[a-z]+$/i.test(color) || /^#[0-9a-fA-F]{3,8}$/.test(color)) return color;
	return undefined;
}
