import "./globals.css";
import { ReactNode } from "react";
import { Providers } from "@/components/providers";

export const metadata = {
  title: "Arabic Center CRM",
  description: "Premium CRM/LMS for Arabic language center",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
