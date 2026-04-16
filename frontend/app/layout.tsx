import "./globals.css";
import { Cairo } from "next/font/google";
import { ReactNode } from "react";
import { Providers } from "@/components/providers";

const cairo = Cairo({ subsets: ["latin", "arabic"], weight: ["400", "500", "600", "700"] });

export const metadata = {
  title: "Arabic Center CRM",
  description: "Premium CRM/LMS for Arabic language center",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={cairo.className}>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
