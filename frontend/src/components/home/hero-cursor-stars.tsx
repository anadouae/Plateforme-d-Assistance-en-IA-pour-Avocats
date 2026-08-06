"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";

type StarSpec = {
  id: number;
  x: number;
  y: number;
  size: number;
  depth: number;
  delay: number;
  tone: number;
};

function buildStars(count: number): StarSpec[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: 8 + Math.random() * 84,
    y: 10 + Math.random() * 80,
    size: 2.5 + Math.random() * 3.5,
    depth: 0.2 + (i % 6) * 0.12,
    delay: Math.random() * 2.4,
    tone: 0.55 + (i % 5) * 0.08,
  }));
}

function StarShape({ size, tone }: { size: number; tone: number }) {
  const gray = Math.round(140 + tone * 70);
  const fill = `rgb(${gray}, ${gray + 4}, ${Math.min(255, gray + 14)})`;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      aria-hidden
      style={{
        filter: `drop-shadow(0 0 ${size * 0.9}px rgba(200, 210, 230, 0.85)) drop-shadow(0 0 ${size * 1.8}px rgba(180, 195, 220, 0.45))`,
      }}
    >
      <path
        d="M12 1.5l2.8 6.4 6.9.6-5.2 4.5 1.6 6.7L12 16.8 5.9 19.7l1.6-6.7-5.2-4.5 6.9-.6L12 1.5z"
        fill={fill}
        opacity={0.75 + tone * 0.15}
      />
    </svg>
  );
}

export function HeroCursorStars({ cursor }: { cursor: { x: number; y: number } }) {
  const stars = useMemo(() => buildStars(40), []);

  return (
    <div className="pointer-events-none absolute inset-0 z-[2] overflow-hidden" aria-hidden>
      {stars.map((star) => {
        const dx = (cursor.x - 0.5) * star.depth * 90;
        const dy = (cursor.y - 0.5) * star.depth * 70;
        return (
          <motion.div
            key={star.id}
            className="absolute will-change-transform"
            style={{
              left: `${star.x}%`,
              top: `${star.y}%`,
            }}
            animate={{
              x: dx,
              y: dy,
              scale: [0.85, 1.25, 0.85],
              opacity: [0.25, 0.95, 0.25],
              rotate: [0, 8, -6, 0],
            }}
            transition={{
              x: { type: "spring", stiffness: 40, damping: 18 },
              y: { type: "spring", stiffness: 40, damping: 18 },
              scale: {
                duration: 2.2 + star.depth,
                repeat: Infinity,
                delay: star.delay,
                ease: "easeInOut",
              },
              opacity: {
                duration: 2.2 + star.depth,
                repeat: Infinity,
                delay: star.delay,
                ease: "easeInOut",
              },
              rotate: {
                duration: 5 + star.depth,
                repeat: Infinity,
                delay: star.delay,
                ease: "easeInOut",
              },
            }}
          >
            <StarShape size={star.size} tone={star.tone} />
          </motion.div>
        );
      })}
    </div>
  );
}
