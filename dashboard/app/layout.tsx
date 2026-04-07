import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Motherbrain MCP Dashboard",
  description: "Control plane for agent orchestration",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <Providers>
          <div className="flex min-h-screen">
            <Nav />
            <main className="flex-1 bg-slate-50 p-6 overflow-auto">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
