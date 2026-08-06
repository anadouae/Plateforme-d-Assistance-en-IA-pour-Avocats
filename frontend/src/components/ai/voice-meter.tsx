"use client";

import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";

/** Barres de fréquence — alimentées par AnalyserNode (temps réel). */
export function VoiceMeter({
  analyser,
  active,
  className,
  bars = 28,
}: {
  analyser: AnalyserNode | null;
  active: boolean;
  className?: string;
  bars?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !analyser || !active) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const data = new Uint8Array(analyser.frequencyBinCount);

    const draw = () => {
      analyser.getByteFrequencyData(data);
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      const barW = width / bars;
      for (let i = 0; i < bars; i++) {
        const idx = Math.floor((i / bars) * data.length);
        const v = data[idx] / 255;
        const h = Math.max(3, v * height * 0.92);
        const x = i * barW + 1;
        const y = (height - h) / 2;
        const grad = ctx.createLinearGradient(0, y, 0, y + h);
        grad.addColorStop(0, "#D2B589");
        grad.addColorStop(1, "#0B1F4A");
        ctx.fillStyle = grad;
        ctx.fillRect(x, y, Math.max(2, barW - 2), h);
      }
      rafRef.current = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [analyser, active, bars]);

  return (
    <canvas
      ref={canvasRef}
      width={480}
      height={56}
      className={cn(
        "h-14 w-full rounded-xl border border-sanad-border bg-sanad-navy/5",
        !active && "opacity-40",
        className,
      )}
      aria-hidden
    />
  );
}
