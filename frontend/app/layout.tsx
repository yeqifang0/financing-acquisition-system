import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "企业融资智能获客系统",
  description: "AI Agent 工作台 — 企查查数据采集 + 8维度融资意向评分",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" className="h-full">
      <body className="h-full flex">
        <Sidebar />
        <main className="flex-1 h-screen overflow-hidden">{children}</main>
      </body>
    </html>
  );
}
