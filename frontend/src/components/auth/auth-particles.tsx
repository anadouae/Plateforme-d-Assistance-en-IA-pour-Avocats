"use client";

import { useEffect, useRef } from "react";

type Particle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  o: number;
  /** 0 bleu, 1 orange vif, 2 blanc soft */
  tone: 0 | 1 | 2;
};

const FILL = [
  (a: number) => `rgba(168,192,255,${a})`,
  (a: number) => `rgba(255,106,0,${a})`,
  (a: number) => `rgba(255,255,255,${a})`,
] as const;

const LINK = [
  (a: number) => `rgba(76,124,255,${a})`,
  (a: number) => `rgba(255,106,0,${a})`,
  (a: number) => `rgba(255,176,122,${a})`,
] as const;

/** Particules auth — bascule pro bleu royal ↔ orange vif */
export function AuthParticles({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let w = 0;
    let h = 0;
    let t0 = performance.now();
    let particles: Particle[] = [];
    const mouse = { x: -9999, y: -9999, active: false };
    const LINK_DIST = 190;
    const COUNT_BASE = 82;

    function resize() {
      const parent = canvas!.parentElement;
      w = parent?.clientWidth || window.innerWidth;
      h = parent?.clientHeight || window.innerHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas!.width = Math.floor(w * dpr);
      canvas!.height = Math.floor(h * dpr);
      canvas!.style.width = `${w}px`;
      canvas!.style.height = `${h}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.max(48, Math.floor((COUNT_BASE * (w * h)) / (1400 * 900)));
      particles = Array.from({ length: n }, () => spawn());
    }

    function spawn(): Particle {
      const roll = Math.random();
      const tone: 0 | 1 | 2 = roll < 0.42 ? 0 : roll < 0.78 ? 1 : 2;
      return {
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.8,
        vy: (Math.random() - 0.5) * 0.8,
        r: 1.15 + Math.random() * 2.5,
        o: 0.3 + Math.random() * 0.5,
        tone,
      };
    }

    function lerp(a: number, b: number, t: number) {
      return a + (b - a) * t;
    }

    function tick(now: number) {
      const elapsed = (now - t0) / 1000;
      // cycle lent ~8s : 0 = bleu, 1 = orange
      const blend = 0.5 + 0.5 * Math.sin(elapsed * (Math.PI * 2) / 8);

      ctx!.clearRect(0, 0, w, h);

      const g = ctx!.createLinearGradient(0, 0, w, h);
      // navy ↔ warm orange wash
      const c1 = {
        r: Math.round(lerp(7, 42, blend)),
        g: Math.round(lerp(16, 18, blend)),
        b: Math.round(lerp(51, 8, blend)),
      };
      const c2 = {
        r: Math.round(lerp(18, 255, blend * 0.55)),
        g: Math.round(lerp(48, 90, blend * 0.45)),
        b: Math.round(lerp(122, 0, blend * 0.7)),
      };
      const c3 = {
        r: Math.round(lerp(10, 28, blend)),
        g: Math.round(lerp(18, 12, blend)),
        b: Math.round(lerp(40, 10, blend)),
      };
      g.addColorStop(0, `rgb(${c1.r},${c1.g},${c1.b})`);
      g.addColorStop(0.5, `rgb(${c2.r},${c2.g},${c2.b})`);
      g.addColorStop(1, `rgb(${c3.r},${c3.g},${c3.b})`);
      ctx!.fillStyle = g;
      ctx!.fillRect(0, 0, w, h);

      // dual auras that trade dominance
      const blueA = ctx!.createRadialGradient(w * 0.25, h * 0.3, 0, w * 0.25, h * 0.3, w * 0.5);
      blueA.addColorStop(0, `rgba(76,124,255,${0.34 * (1 - blend)})`);
      blueA.addColorStop(1, "transparent");
      ctx!.fillStyle = blueA;
      ctx!.fillRect(0, 0, w, h);

      const orangeA = ctx!.createRadialGradient(w * 0.75, h * 0.35, 0, w * 0.75, h * 0.35, w * 0.48);
      orangeA.addColorStop(0, `rgba(255,106,0,${0.32 * blend})`);
      orangeA.addColorStop(1, "transparent");
      ctx!.fillStyle = orangeA;
      ctx!.fillRect(0, 0, w, h);

      const softOrange = ctx!.createRadialGradient(w * 0.45, h * 0.85, 0, w * 0.45, h * 0.85, w * 0.4);
      softOrange.addColorStop(0, `rgba(255,176,122,${0.16 * (0.4 + blend * 0.6)})`);
      softOrange.addColorStop(1, "transparent");
      ctx!.fillStyle = softOrange;
      ctx!.fillRect(0, 0, w, h);

      for (const p of particles) {
        // soft bias: particles drift toward dominant color zones
        if (p.tone === 0) p.vx += (1 - blend) * 0.002;
        if (p.tone === 1) p.vx -= blend * 0.002;

        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;

        if (mouse.active) {
          const dx = p.x - mouse.x;
          const dy = p.y - mouse.y;
          const d = Math.hypot(dx, dy);
          if (d < 160 && d > 0.01) {
            p.vx += (dx / d) * 0.024;
            p.vy += (dy / d) * 0.024;
            p.r = Math.min(6.2, p.r + 0.03);
          } else {
            p.r += (2 - p.r) * 0.02;
          }
        }

        const pulse =
          p.tone === 1
            ? 0.75 + 0.25 * blend
            : p.tone === 0
              ? 0.75 + 0.25 * (1 - blend)
              : 0.85;
        ctx!.beginPath();
        ctx!.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx!.fillStyle = FILL[p.tone](p.o * pulse);
        ctx!.fill();
      }

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d = Math.hypot(dx, dy);
          if (d < LINK_DIST) {
            const alpha = (1 - d / LINK_DIST) * 0.38;
            const tone =
              a.tone === 1 || b.tone === 1
                ? 1
                : a.tone === 0 || b.tone === 0
                  ? 0
                  : 2;
            const boost = tone === 1 ? 0.55 + blend * 0.45 : 0.55 + (1 - blend) * 0.45;
            ctx!.strokeStyle = LINK[tone](alpha * boost);
            ctx!.lineWidth = tone === 1 ? 1.2 : 1;
            ctx!.beginPath();
            ctx!.moveTo(a.x, a.y);
            ctx!.lineTo(b.x, b.y);
            ctx!.stroke();
          }
        }
      }

      raf = requestAnimationFrame(tick);
    }

    function onMove(e: MouseEvent) {
      const rect = canvas!.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
      mouse.active = true;
    }
    function onLeave() {
      mouse.active = false;
    }
    function onClick() {
      for (let i = 0; i < 5; i++) particles.push(spawn());
      if (particles.length > 160) particles.splice(0, 5);
    }

    resize();
    raf = requestAnimationFrame(tick);
    window.addEventListener("resize", resize);
    canvas.addEventListener("mousemove", onMove);
    canvas.addEventListener("mouseleave", onLeave);
    canvas.addEventListener("click", onClick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("mousemove", onMove);
      canvas.removeEventListener("mouseleave", onLeave);
      canvas.removeEventListener("click", onClick);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={className}
      aria-hidden
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", display: "block" }}
    />
  );
}
