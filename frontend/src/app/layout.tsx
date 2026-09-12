import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { Cairo, Fraunces, Inter, IBM_Plex_Mono } from "next/font/google";
import { LocaleProvider } from "@/components/providers/locale-provider";
import "./globals.css";
import "@/styles/lexhub-ui.css";
import "@/styles/glass-redaction.css";
import "@/styles/auth-glass.css";

const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: "--font-cairo",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-inter",
  display: "swap",
  preload: true,
});

const fraunces = Fraunces({
  subsets: ["latin"],
  weight: ["500", "600"],
  variable: "--font-fraunces",
  display: "swap",
  preload: true,
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-plex-mono",
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  title: "LexHub — LegalTech pour cabinets marocains",
  description:
    "LexHub : plaidoirie vocale, dossiers et synthèse documentaire pour cabinets d'avocats au Maroc.",
  applicationName: "LexHub",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "LexHub",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [{ url: "/logo-lexhub-cube.png", type: "image/png" }],
    apple: "/logo-lexhub-cube.png",
  },
  other: {
    "mobile-web-app-capable": "yes",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#EEF1F8" },
    { media: "(prefers-color-scheme: dark)", color: "#0A1228" },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      dir="ltr"
      suppressHydrationWarning
      className={`${cairo.variable} ${inter.variable} ${fraunces.variable} ${plexMono.variable}`}
    >
      <body className="font-sans antialiased" suppressHydrationWarning>
        <Script id="lexhub-prefs" strategy="beforeInteractive">
          {`try{var t=localStorage.getItem('lexhub-ui-theme');if(t==='dark')document.documentElement.dataset.theme='dark';var d=localStorage.getItem('lexhub-ui-density');if(d)document.documentElement.dataset.density=d;}catch(e){}`}
        </Script>
        <LocaleProvider>{children}</LocaleProvider>
      </body>
    </html>
  );
}
