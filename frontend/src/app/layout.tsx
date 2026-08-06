import type { Metadata } from "next";
import { Cairo } from "next/font/google";
import { LocaleProvider } from "@/components/providers/locale-provider";
import "./globals.css";

const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: "--font-cairo",
  display: "swap",
});

export const metadata: Metadata = {
  title: "سند — حركتان. والباقي يتبع.",
  description:
    "سند منصة LegalTech للمكاتب المغربية: إملاء المرافعة وتلخيص الوثائق في مسار واحد.",
  icons: {
    icon: [{ url: "/logo-sanad.png", type: "image/png" }],
    apple: "/logo-sanad.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl" className={cairo.variable}>
      <body className="font-serif antialiased">
        <LocaleProvider>{children}</LocaleProvider>
      </body>
    </html>
  );
}
