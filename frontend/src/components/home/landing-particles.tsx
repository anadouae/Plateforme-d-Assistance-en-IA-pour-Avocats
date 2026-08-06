"use client";

import { useEffect, useRef } from "react";

/** Particules flottantes du hero v3. */
export function LandingParticles() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const field = ref.current;
    if (!field) return;
    const NUM = 24;
    const particles = Array.from({ length: NUM }, () => {
      const el = document.createElement("div");
      el.className = "absolute rounded-full bg-[#D9BA6A] opacity-35 pointer-events-none";
      field.appendChild(el);
      return {
        el,
        x: Math.random() * 100,
        y: Math.random() * 100,
        speed: 0.006 + Math.random() * 0.014,
        drift: (Math.random() - 0.5) * 0.02,
        size: 2 + Math.random() * 2.5,
      };
    });
    particles.forEach((p) => {
      p.el.style.width = `${p.size}px`;
      p.el.style.height = `${p.size}px`;
    });
    let raf = 0;
    const tick = () => {
      particles.forEach((p) => {
        p.y -= p.speed;
        p.x += p.drift;
        if (p.y < -2) {
          p.y = 102;
          p.x = Math.random() * 100;
        }
        p.el.style.left = `${p.x}%`;
        p.el.style.top = `${p.y}%`;
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      particles.forEach((p) => p.el.remove());
    };
  }, []);

  return <div ref={ref} className="pointer-events-none absolute inset-0 z-0" aria-hidden />;
}
