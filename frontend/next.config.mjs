/** @type {import('next').NextConfig} */
const isProd = process.env.NODE_ENV === "production";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value:
      "camera=(), geolocation=(), payment=(), usb=(), interest-cohort=(), microphone=(self)",
  },
  { key: "X-XSS-Protection", value: "1; mode=block" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
  { key: "Cross-Origin-Resource-Policy", value: "same-site" },
  { key: "X-DNS-Prefetch-Control", value: "on" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://challenges.cloudflare.com https://accounts.google.com",
      "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
      "font-src 'self' https://fonts.gstatic.com data:",
      "img-src 'self' data: blob: https:",
      "connect-src 'self' http://localhost:8001 http://127.0.0.1:8001 https:",
      "media-src 'self' blob:",
      "worker-src 'self' blob:",
      "frame-src https://challenges.cloudflare.com https://accounts.google.com",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "object-src 'none'",
      "upgrade-insecure-requests",
    ].join("; "),
  },
];

if (isProd) {
  securityHeaders.push({
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  });
}

const nextConfig = {
  poweredByHeader: false,
  compress: true,
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  transpilePackages: ["three", "@react-three/fiber", "@react-three/drei"],
  // Dev derrière Caddy (lexhub.space) — évite warnings / soucis de chunks
  allowedDevOrigins: ["lexhub.space", "www.lexhub.space", "https://lexhub.space", "https://www.lexhub.space"],
  experimental: {
    optimizePackageImports: ["lucide-react", "framer-motion"],
  },
  async redirects() {
    return [
      { source: "/home", destination: "/dashboard", permanent: false },
      { source: "/sanad-landing-v3.html", destination: "/", permanent: true },
    ];
  },
  async rewrites() {
    return [{ source: "/favicon.ico", destination: "/logo-lexhub-cube.png" }];
  },
  async headers() {
    const staticCache = isProd
      ? [
          {
            source: "/_next/static/:path*",
            headers: [
              {
                key: "Cache-Control",
                value: "public, max-age=31536000, immutable",
              },
            ],
          },
        ]
      : [
          {
            source: "/_next/static/:path*",
            headers: [
              {
                key: "Cache-Control",
                value: "no-store, must-revalidate",
              },
            ],
          },
        ];

    return [
      {
        source: "/:path*",
        headers: securityHeaders,
      },
      {
        source: "/",
        headers: [{ key: "Cache-Control", value: "no-store, must-revalidate" }],
      },
      {
        source: "/(login|register|forgot-password|reset-password|activate)",
        headers: [{ key: "Cache-Control", value: "no-store" }],
      },
      ...staticCache,
      {
        source: "/logo-:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=86400, stale-while-revalidate=604800",
          },
        ],
      },
    ];
  },
  webpack: (config) => {
    config.externals = [...(config.externals || []), { canvas: "canvas" }];
    return config;
  },
};

export default nextConfig;
