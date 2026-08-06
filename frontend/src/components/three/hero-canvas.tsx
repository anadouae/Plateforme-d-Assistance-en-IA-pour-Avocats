"use client";

import { Component, type ReactNode, useEffect, useState } from "react";
import dynamic from "next/dynamic";

function HeroFallback() {
  return (
    <div className="absolute inset-0 bg-gradient-to-br from-sanad-navy via-[#1a223d] to-sanad-navy">
      <div className="sanad-orb sanad-orb-1" />
      <div className="sanad-orb sanad-orb-2" />
      <div className="sanad-orb sanad-orb-3" />
    </div>
  );
}

const HeroScene = dynamic(
  () =>
    import("./scene")
      .then((m) => ({ default: m.HeroScene }))
      .catch(() => ({ default: HeroFallback })),
  {
    ssr: false,
    loading: () => <HeroFallback />,
  },
);

class HeroSceneBoundary extends Component<
  { children: ReactNode; cursor?: { x: number; y: number } },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch() {
    /* chunk load / WebGL failures — keep hero usable */
  }

  render() {
    if (this.state.failed) return <HeroFallback />;
    return this.props.children;
  }
}

export function HeroCanvas({ cursor }: { cursor?: { x: number; y: number } }) {
  const [ready, setReady] = useState(false);

  // Avoid racing HMR / stale chunks right after reload
  useEffect(() => {
    const t = window.setTimeout(() => setReady(true), 50);
    return () => window.clearTimeout(t);
  }, []);

  if (!ready) return <HeroFallback />;

  return (
    <HeroSceneBoundary>
      <HeroScene cursor={cursor} />
    </HeroSceneBoundary>
  );
}
