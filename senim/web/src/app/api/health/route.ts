import { API, backendHeaders } from "@/lib/backend";

export const dynamic = "force-dynamic";

// Only what the UI needs. The backend's llm_key_preview (a masked piece of the API key) and model
// config stay server-side, because this route is reachable by anyone with the public link.
const PUBLIC_FIELDS = ["llm", "search", "author_models", "max_input_chars"] as const;

export async function GET() {
  try {
    const res = await fetch(`${API}/api/health`, { cache: "no-store", headers: backendHeaders(), signal: AbortSignal.timeout(5000) });
    const full = (await res.json()) as Record<string, unknown>;
    const safe = Object.fromEntries(PUBLIC_FIELDS.filter((k) => k in full).map((k) => [k, full[k]]));
    return Response.json(safe, { status: res.status });
  } catch {
    return Response.json({ code: "backend_unreachable" }, { status: 502 });
  }
}
