import type { Metadata } from "next";
import { Cairo, Fraunces, Inter, IBM_Plex_Mono } from "next/font/google";
import { LocaleProvider } from "@/components/providers/locale-provider";
import "./globals.css";
import "@/styles/sanad-ui.css";
import "@/styles/glass-redaction.css";
import "@/styles/auth-glass.css";

const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: "--font-cairo",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-inter",
  display: "swap",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["300", "500", "600"],
  variable: "--font-fraunces",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-plex-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "سند — حركتان. والباقي يتبع.",
  description:
    "سند منصة LegalTech للمكاتب المغربية: إملاء المرافعة وتلخيص الوثائق في مسار واحد.",
  applicationName: "سند",
  manifest: "/manifest.json",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F7F5F0" },
    { media: "(prefers-color-scheme: dark)", color: "#0E1526" },
  ],
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "سند",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [{ url: "/logo-sanad-cube.png", type: "image/png" }],
    apple: "/logo-sanad-cube.png",
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ar"
      dir="rtl"
      className={`${cairo.variable} ${inter.variable} ${fraunces.variable} ${plexMono.variable}`}
    >
      <body className="font-sans antialiased">
        <LocaleProvider>{children}</LocaleProvider>
      </body>
    </html>
  );
}
