import type { Metadata } from "next";
import { Inter } from "next/font/google";

import Navbar from '@/components/Navbar';
import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Create Next App",
  description: "Generated by create next app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} w-full min-h-screen flex flex-col`}>
        <Navbar />
        <main className="flex flex-grow items-center">{children}</main>
      </body>
    </html >
  );
}