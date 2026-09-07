import type { NextConfig } from "next";

// 根据 API_BASE 决定是否需要 rewrite 代理
// - 本地开发: NEXT_PUBLIC_API_BASE=/api  → 代理到 localhost:8001
// - Render 生产: NEXT_PUBLIC_API_BASE=https://xxx.onrender.com/api → 直接 fetch（后端已开 CORS）
const apiBase = process.env.NEXT_PUBLIC_API_BASE || "/api";
const needsRewrite = !apiBase.startsWith("http");

const nextConfig: NextConfig = {
  // 仅当 NEXT_PUBLIC_API_BASE 是相对路径时（本地开发），才代理到后端
  ...(needsRewrite
    ? {
        async rewrites() {
          return [
            {
              source: "/api/:path*",
              destination: "http://localhost:8001/api/:path*",
            },
          ];
        },
      }
    : {}),
  allowedDevOrigins: [
    "localhost",
    "localhost:3000",
    "127.0.0.1:3000",
  ],
};

export default nextConfig;
