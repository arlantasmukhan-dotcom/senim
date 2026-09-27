// Streams the FastAPI Server-Sent Events through unchanged, so the browser only talks to Next.
import { API, backendHeaders } from "@/lib/backend";

export const dynamic = "force-dynamic";
// A full check takes 30-40 s; leave headroom so hosting platforms do not cut the stream.
export const maxDuration = 300;

export async function POST(req: Request) {
  let upstream: Response;
  try {
    upstream = await fetch(`${API}/api/check`, {
      method: "POST",
      headers: backendHeaders({ "content-type": "application/json" }),
      body: await req.text(),
      signal: req.signal,
      cache: "no-store",
    });
  } catch {
    return Response.json({ code: "backend_unreachable" }, { status: 502 });
  }
  if (!upstream.ok || !upstream.body) {
    return Response.json({ code: "backend_error", status: upstream.status }, { status: 502 });
  }
  return new Response(upstream.body, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      "x-accel-buffering": "no",
    },
  });
}
