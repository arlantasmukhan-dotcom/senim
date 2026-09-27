// Server-only: where the FastAPI backend lives and how this app proves it is the caller.
// SENIM_PROXY_TOKEN is set on public deployments; the backend rejects /api/* calls without it.
export const API = process.env.SENIM_API_URL ?? "http://127.0.0.1:8000";

export function backendHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const token = process.env.SENIM_PROXY_TOKEN;
  return token ? { ...extra, "x-senim-token": token } : extra;
}
