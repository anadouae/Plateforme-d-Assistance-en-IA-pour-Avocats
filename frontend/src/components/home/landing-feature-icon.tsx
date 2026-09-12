"use client";

import { motion } from "framer-motion";
import { Activity, FileText, Mic, Users } from "lucide-react";

export function LandingFeatureIcon({ kind, dark }: { kind: "mic" | "file" | "synth" | "team"; dark: boolean }) {
  const cls = dark ? "text-[#A8C0FF]" : "text-[#12307A]";

  if (kind === "mic") {
    return (
      <div className="relative flex h-[52px] w-[52px] items-end justify-center gap-1">
        <Mic className={`absolute -top-1 h-8 w-8 ${cls}`} strokeWidth={1.4} />
        {[0, 1, 2, 3, 4].map((i) => (
          <motion.span
            key={i}
            className="w-1 rounded-full bg-[#4C7CFF]"
            animate={{ height: [8, 22 + i * 3, 10, 18, 8] }}
            transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.08, ease: "easeInOut" }}
          />
        ))}
      </div>
    );
  }

  if (kind === "file") {
    return (
      <div className="relative h-14 w-12">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className={`absolute inset-x-0 rounded-md border ${dark ? "border-[#4C7CFF]/40 bg-[#0B1A4D]" : "border-[#12307A]/20 bg-white"}`}
            style={{ height: 44, top: i * 4 }}
            animate={{ y: [0, -2, 0], opacity: [0.7, 1, 0.7] }}
            transition={{ duration: 2.2, repeat: Infinity, delay: i * 0.25 }}
          />
        ))}
        <FileText className={`absolute bottom-0 left-1/2 h-8 w-8 -translate-x-1/2 ${cls}`} strokeWidth={1.4} />
      </div>
    );
  }

  if (kind === "synth") {
    return (
      <div className="flex flex-col gap-1.5">
        <Activity className={`h-8 w-8 ${cls}`} strokeWidth={1.4} />
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className={`h-1 rounded ${dark ? "bg-[#4C7CFF]/60" : "bg-[#12307A]/30"}`}
            initial={{ width: 0 }}
            animate={{ width: ["0%", "100%", "70%"] }}
            transition={{ duration: 2, repeat: Infinity, delay: i * 0.35 }}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className={`flex h-10 w-10 items-center justify-center rounded-full border ${dark ? "border-[#4C7CFF]/50 bg-[#12307A]" : "border-[#12307A]/20 bg-white"}`}
          initial={{ scale: 0.6, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse", delay: i * 0.35 }}
        >
          <Users className={`h-4 w-4 ${cls}`} strokeWidth={1.6} />
        </motion.div>
      ))}
    </div>
  );
}
