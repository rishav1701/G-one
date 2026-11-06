import {useCallback} from 'react';

let csrfToken = '';
export function setCsrfToken(value: string) { csrfToken = value; }
export class ApiError extends Error {
  requestId: string;
  status: number;
  constructor(message: string, requestId: string, status: number) {
    super(message); this.name = 'ApiError'; this.requestId = requestId; this.status = status;
  }
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = (init.method || 'GET').toUpperCase();
  const headers = new Headers(init.headers); headers.set('Accept', 'application/json');
  if (init.body) headers.set('Content-Type', 'application/json');
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method) && csrfToken) headers.set('X-CSRF-Token', csrfToken);
  const response = await fetch(`/api/v1${path}`, { ...init, headers, credentials: 'include' });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = typeof payload.message === 'string' ? payload.message : typeof payload.detail === 'string' ? payload.detail : 'Request failed';
    throw new ApiError(message, payload.request_id || response.headers.get('X-Request-ID') || 'Unavailable', response.status);
  }
  if (payload.csrf_token) setCsrfToken(payload.csrf_token);
  return payload as T;
}
export function useApi() { return useCallback(api, []); }
