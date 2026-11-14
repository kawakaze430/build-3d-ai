import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Build 3D AI Studio",
  description: "Private browser studio for durable Build 3D AI projects and verified GLB artifacts.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
