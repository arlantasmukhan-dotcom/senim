// Streams the FastAPI Server-Sent Events through unchanged, so the browser only talks to Next.
import { API, backendHeaders } from "@/lib/backend";

export const dynamic = "force-dynamic";
// A full check takes 30-40 s; leave headroom so hosting platforms do not cut the stream.
export const maxDuration = 300;

// The visitor's IP, for the backend's per-IP rate limit. Read only headers the platform itself sets:
// Vercel overwrites x-real-ip / x-forwarded-for; Cloudflare (share.sh tunnel) overwrites cf-connecting-ip.
function clientIp(req: Request): string {
  const h = req.headers;
  const ip = process.env.VERCEL
    ? h.get("x-real-ip") ?? h.get("x-forwarded-for")?.split(",")[0]
    : h.get("cf-connecting-ip") ?? h.get("x-forwarded-for")?.split(",")[0];
  return (ip ?? "").trim();
}

export async function POST(req: Request) {
  let upstream: Response;
  try {
    upstream = await fetch(`${API}/api/check`, {
      method: "POST",
      headers: backendHeaders({ "content-type": "application/json", "x-senim-client-ip": clientIp(req) }),
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
