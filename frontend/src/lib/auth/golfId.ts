/** Golf-ID format: 6 digits, dash, 3 digits — e.g. `123456-789`. */
export const GOLF_ID_REGEX = /^\d{6}-\d{3}$/;

export function isValidGolfId(s: string): boolean {
	return GOLF_ID_REGEX.test(s);
}

/**
 * Auto-format a raw input string into Golf-ID format.
 * - Strips all non-digit characters.
 * - Inserts a dash after the 6th digit.
 * - Caps total length at 10 characters (`XXXXXX-XXX`).
 *
 * @example
 * formatGolfId('123456789')  // '123456-789'
 * formatGolfId('123456-789') // '123456-789'
 * formatGolfId('abc12')      // '12'
 */
export function formatGolfId(input: string): string {
	const digits = input.replace(/\D/g, '').slice(0, 9);
	if (digits.length <= 6) return digits;
	return `${digits.slice(0, 6)}-${digits.slice(6)}`;
}
