import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // gzip would buffer the Server-Sent Events stream from /api/check.
  compress: false,
  // ./share.sh serves the dev server through a Cloudflare quick tunnel (random *.trycloudflare.com host).
  allowedDevOrigins: ["*.trycloudflare.com"],
};

export default nextConfig;
