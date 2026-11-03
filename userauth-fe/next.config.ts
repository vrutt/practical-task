import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL;
if (!backendUrl) throw new Error("BACKEND_URL must be configured in .env.local");

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/docs", destination: `${backendUrl}/docs` },
      { source: "/api/openapi.json", destination: `${backendUrl}/openapi.json` },
      { source: "/api/:path*", destination: `${backendUrl}/api/:path*` },
    ];
  },
};
export default nextConfig;
