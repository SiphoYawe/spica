import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker production builds
  output: "standalone",

  // Image optimization settings
  images: {
    remotePatterns: [],
    unoptimized: false,
  },

  // Environment variables available at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // React strict mode
  reactStrictMode: true,
};

export default nextConfig;
