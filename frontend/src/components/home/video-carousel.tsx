"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export const HERO_VIDEOS = [
  "/videos/hero-desk.mp4", // premier plan stable (évite « 2 versions » au refresh)
  "/videos/popup-brand.mp4",
  "/videos/popup-justice.mp4",
] as const;

export const POPUP_VIDEOS = [
  "/videos/popup-justice.mp4",
  "/videos/popup-brand.mp4",
  "/videos/popup-workspace.mp4",
] as const;

type CarouselProps = {
  sources: readonly string[];
  className?: string;
  intervalMs?: number;
  /** Overlay sombre pour lisibilité / branding */
  overlayClassName?: string;
};

/** Carousel vidéo muet en boucle (Pexels compressés 720p). */
export function VideoCarousel({
  sources,
  className,
  intervalMs = 9000,
  overlayClassName = "bg-gradient-to-t from-[#071033]/85 via-[#071033]/35 to-[#0B1A4D]/25",
}: CarouselProps) {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    if (sources.length < 2) return;
    const t = window.setInterval(() => {
      setIdx((i) => (i + 1) % sources.length);
    }, intervalMs);
    return () => window.clearInterval(t);
  }, [sources.length, intervalMs]);

  return (
    <div className={cn("relative overflow-hidden bg-[#071033]", className)}>
      {sources.map((src, i) => (
        <video
          key={src}
          className={cn(
            "absolute inset-0 h-full w-full object-cover transition-opacity duration-1000",
            i === idx ? "opacity-100" : "opacity-0",
          )}
          src={src}
          muted
          playsInline
          autoPlay
          loop
          preload={i === 0 ? "auto" : "metadata"}
          aria-hidden
        />
      ))}
      <div className={cn("pointer-events-none absolute inset-0", overlayClassName)} aria-hidden />
      {sources.length > 1 ? (
        <div className="absolute bottom-4 left-1/2 z-[1] flex -translate-x-1/2 gap-1.5">
          {sources.map((src, i) => (
            <button
              key={src}
              type="button"
              aria-label={`Vidéo ${i + 1}`}
              className={cn(
                "h-1.5 w-1.5 rounded-full transition-all",
                i === idx ? "w-4 bg-[#FF6A00]" : "bg-white/40 hover:bg-white/70",
              )}
              onClick={() => setIdx(i)}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
