"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface ImagesBadgeProps {
  text: string;
  images: string[];
  className?: string;
  folderSize?: { width: number; height: number };
  teaserImageSize?: { width: number; height: number };
  hoverImageSize?: { width: number; height: number };
  hoverTranslateY?: number;
  hoverSpread?: number;
}

export function ImagesBadge({
  text,
  images,
  className,
  folderSize = { width: 48, height: 36 },
  teaserImageSize = { width: 40, height: 28 },
  hoverImageSize = { width: 140, height: 108 },
  hoverTranslateY = -110,
  hoverSpread = 50,
}: ImagesBadgeProps) {
  return (
    <motion.div
      className={cn(
        "group relative inline-flex items-center gap-3 rounded-full border border-sanad-gold/35 bg-white/10 px-4 py-2 text-sm text-white backdrop-blur-md",
        className,
      )}
      whileHover="hover"
      initial="rest"
    >
      <div
        className="relative"
        style={{ width: folderSize.width, height: folderSize.height }}
      >
        {images.slice(0, 3).map((src, i) => (
          <motion.div
            key={src + i}
            className="absolute overflow-hidden rounded-md border border-white/30 shadow-md"
            style={{
              width: teaserImageSize.width,
              height: teaserImageSize.height,
              left: i * 8,
              top: i * 2,
              zIndex: 3 - i,
            }}
            variants={{
              rest: { y: 0, x: 0, scale: 1, rotate: i * -4 },
              hover: {
                y: hoverTranslateY,
                x: (i - 1) * hoverSpread,
                scale: hoverImageSize.width / teaserImageSize.width,
                rotate: (i - 1) * 8,
              },
            }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
          >
            <Image
              src={src}
              alt=""
              width={hoverImageSize.width}
              height={hoverImageSize.height}
              className="h-full w-full object-cover"
              unoptimized
            />
          </motion.div>
        ))}
      </div>
      <span className="font-medium tracking-wide">{text}</span>
    </motion.div>
  );
}
