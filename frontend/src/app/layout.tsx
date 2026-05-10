import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/sidebar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AutoPermit AI — Building Permit Verification",
  description:
    "Automated municipal building permit verification using YOLOv8 computer vision and GPT-4o compliance analysis. Upload architectural blueprints for instant code compliance checks.",
  keywords: [
    "building permit",
    "compliance",
    "blueprint analysis",
    "AI verification",
    "YOLOv8",
    "municipal code",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans bg-gradient-radial min-h-screen`}
      >
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 overflow-y-auto">
            <div className="bg-grid min-h-screen">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
