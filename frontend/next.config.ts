import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 将 /api/* 代理到后端，消除 CORS 依赖
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8001/api/:path*",
      },
    ];
  },
  allowedDevOrigins: [
    "localhost",
    "localhost:3000",
    "127.0.0.1:3000",
    "*.remote-agent.svc.cluster.local",
    "*.svc.cluster.local",
  ],
};

export default nextConfig;
