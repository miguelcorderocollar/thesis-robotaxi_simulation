import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Robotaxi thesis lab",
  description: "Browser-based Monte Carlo model for the Tesla Robotaxi thesis.",
  icons: { icon: "/robotaxi-outline.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
