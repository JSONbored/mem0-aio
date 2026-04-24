/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  skipTrailingSlashRedirect: true,
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: "/openmemory-api/api/v1/config",
        destination: "http://127.0.0.1:8765/api/v1/config/",
      },
      {
        source: "/openmemory-api/api/v1/memories",
        destination: "http://127.0.0.1:8765/api/v1/memories/",
      },
      {
        source: "/openmemory-api/api/v1/apps",
        destination: "http://127.0.0.1:8765/api/v1/apps/",
      },
      {
        source: "/openmemory-api/api/v1/stats",
        destination: "http://127.0.0.1:8765/api/v1/stats/",
      },
      {
        source: "/openmemory-api/:path*",
        destination: "http://127.0.0.1:8765/:path*",
      },
    ];
  },
};

export default nextConfig;
