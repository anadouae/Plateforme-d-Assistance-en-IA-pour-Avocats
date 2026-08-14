"use client";

import { cn } from "@/lib/utils";

/** Orbe liquide — classes `.orb` / `.listening` exactes (filtre `#goo` dans AppShell). */
export function VoiceOrb({
  listening = false,
  className,
}: {
  listening?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("orb", listening && "listening", className)} aria-hidden>
      <span />
      <span />
      <span />
    </div>
  );
}

export function VoiceWave({
  active = false,
  className,
}: {
  active?: boolean;
  className?: string;
}) {
  return (
    <div className={cn("wave", active && "is-listening", className)} aria-hidden>
      {Array.from({ length: 12 }).map((_, i) => (
        <i key={i} />
      ))}
    </div>
  );
}
