import type { Metadata } from "react";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Multi-Agent Voice Trip Planner",
  description: "AI-powered Travel Planner Orchestrated by Multiple Agents",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans bg-[#121212] text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
