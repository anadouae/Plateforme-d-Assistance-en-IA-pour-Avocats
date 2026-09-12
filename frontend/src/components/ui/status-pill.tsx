import { cn } from "@/lib/utils";

type Tone = "gold" | "emerald" | "ink" | "muted";

const tones: Record<Tone, string> = {
  gold: "bg-[rgba(255,106,0,0.16)] text-[#E85A00]",
  emerald: "bg-[rgba(31,111,84,0.14)] text-[#155943]",
  ink: "bg-[rgba(14,21,38,0.08)] text-sanad-inkSoft",
  muted: "bg-sanad-stone/80 text-sanad-inkSoft",
};

export function StatusPill({
  children,
  tone = "gold",
  shimmer = true,
  className,
}: {
  children: React.ReactNode;
  tone?: Tone;
  shimmer?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "relative inline-flex overflow-hidden rounded-full px-2.5 py-1 text-[11px] font-bold",
        tones[tone],
        className,
      )}
    >
      {shimmer && (
        <span
          aria-hidden
          className="pointer-events-none absolute inset-y-0 w-2/5 animate-[status-shimmer_2.4s_linear_infinite] bg-gradient-to-r from-transparent via-white/70 to-transparent motion-reduce:animate-none"
          style={{ left: "-40%" }}
        />
      )}
      <span className="relative z-[1]">{children}</span>
    </span>
  );
}
