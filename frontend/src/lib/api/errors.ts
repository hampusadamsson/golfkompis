export type ApiErrorCode =
	| 'unauthorized' // 401
	| 'bad_request' // 400
	| 'not_found' // 404
	| 'conflict' // 409
	| 'validation' // 422
	| 'upstream' // 502
	| 'network' // fetch() threw (no response)
	| 'unknown'; // any other status

function codeFromStatus(status: number): ApiErrorCode {
	if (status === 400) return 'bad_request';
	if (status === 401) return 'unauthorized';
	if (status === 404) return 'not_found';
	if (status === 409) return 'conflict';
	if (status === 422) return 'validation';
	if (status === 502) return 'upstream';
	return 'unknown';
}

export class ApiError extends Error {
	readonly status: number;
	readonly code: ApiErrorCode;
	/** Parsed response body, if any. For 422 this is `ValidationErrorDetail[]`. */
	readonly details?: unknown;

	constructor(opts: { status: number; code?: ApiErrorCode; message: string; details?: unknown }) {
		super(opts.message);
		this.name = 'ApiError';
		this.status = opts.status;
		this.code = opts.code ?? codeFromStatus(opts.status);
		this.details = opts.details;
	}

	/** Build from a failed fetch Response. */
	static async fromResponse(res: Response): Promise<ApiError> {
		// Read body once as text, then attempt JSON parse.
		// Two separate awaits on the same Response body cause "body already used".
		let body: unknown;
		try {
			const text = await res.text();
			try {
				body = JSON.parse(text);
			} catch {
				body = text || undefined;
			}
		} catch {
			body = undefined;
		}

		// Extract a readable message from HTTPValidationError, plain string, or object
		let message = res.statusText || `HTTP ${res.status}`;
		if (body && typeof body === 'object' && 'detail' in body) {
			const detail = (body as { detail: unknown }).detail;
			if (typeof detail === 'string') {
				message = detail;
			} else if (Array.isArray(detail) && detail.length > 0) {
				message = detail
					.map((d: { msg?: string; loc?: unknown[] }) =>
						d.loc ? `${d.loc.join('.')}: ${d.msg ?? ''}` : (d.msg ?? '')
					)
					.filter(Boolean)
					.join('; ');
			} else if (detail && typeof detail === 'object') {
				// Object-shaped detail (e.g. custom FastAPI handlers)
				message = JSON.stringify(detail);
			}
		} else if (typeof body === 'string' && body) {
			message = body;
		}

		return new ApiError({
			status: res.status,
			message,
			details: body
		});
	}

	static network(cause: unknown): ApiError {
		const message = cause instanceof Error ? cause.message : 'Nätverksfel';
		return new ApiError({ status: 0, code: 'network', message });
	}
}

/**
 * Maps an ApiError (or unknown thrown value) to a user-facing Swedish message.
 * Pass an optional `overrides` map to customise specific codes.
 */
export function getErrorMessage(
	err: unknown,
	overrides: Partial<Record<ApiErrorCode | 'default', string>> = {}
): string {
	const defaults: Record<ApiErrorCode | 'default', string> = {
		unauthorized: 'Sessionen har gått ut. Logga in igen.',
		network: 'Kunde inte nå servern. Kontrollera din anslutning.',
		upstream: 'MinGolf är inte tillgängligt just nu. Försök igen senare.',
		not_found: 'Hittades inte.',
		conflict: 'Tiden bokades precis. Försök med en annan.',
		bad_request: 'Ogiltig förfrågan.',
		validation: 'Valideringsfel.',
		unknown: 'Något gick fel.',
		default: 'Något gick fel.',
	};
	const messages = { ...defaults, ...overrides };
	if (err instanceof ApiError) {
		return messages[err.code] ?? err.message ?? messages.default;
	}
	return messages.default;
}
