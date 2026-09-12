"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

const BARS = 56;

/** Hero vocal : onde live (sans citation factice). */
export function LandingWaveform({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let t = 0;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const draw = () => {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      ctx.clearRect(0, 0, w, h);
      t += 0.028;
      const mid = h / 2;
      const gap = w / BARS;
      for (let i = 0; i < BARS; i++) {
        const x = gap * i + gap * 0.35;
        const dist = Math.abs(i - BARS / 2) / (BARS / 2);
        const envelope = 1 - dist * 0.62;
        const wave =
          Math.sin(t * 2.1 + i * 0.22) * 0.55 +
          Math.sin(t * 3.4 + i * 0.41) * 0.28 +
          Math.sin(t * 0.7 + i * 0.08) * 0.18;
        const barH = Math.max(6, (22 + wave * 38) * envelope);
        const y = mid - barH / 2;
        const g = ctx.createLinearGradient(x, y, x, y + barH);
        g.addColorStop(0, "rgba(255,176,122,0.95)");
        g.addColorStop(0.45, "rgba(255,106,0,1)");
        g.addColorStop(1, "rgba(232,90,0,0.85)");
        ctx.fillStyle = g;
        ctx.shadowColor = "rgba(255,106,0,0.45)";
        ctx.shadowBlur = 10;
        const bw = Math.max(3, gap * 0.38);
        ctx.fillRect(x, y, bw, barH);
      }
      raf = window.requestAnimationFrame(draw);
    };
    raf = window.requestAnimationFrame(draw);
    return () => {
      window.cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <div className={cn("mx-auto mt-10 w-full max-w-[680px]", className)}>
      <canvas ref={canvasRef} className="h-[108px] w-full" aria-hidden />
      <p className="mt-3 text-center text-[12px] font-medium tracking-wide text-[#A8C0FF]/85">
        Dictée arabe · dossier · plaidoirie — LexHub structure, sans inventer
      </p>
    </div>
  );
}
