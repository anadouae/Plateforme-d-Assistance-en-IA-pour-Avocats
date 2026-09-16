"use client";

import { useEffect, useId, useMemo, useRef, type ReactNode } from "react";
import Link from "next/link";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { POPUP_VIDEOS } from "@/components/home/video-carousel";

export type LexProductModalProps = {
  open: boolean;
  onClose: () => void;
  tag: string;
  title: string;
  points?: string[];
  primaryLabel: string;
  primaryHref?: string;
  onPrimary?: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
  /** Contenu optionnel sous les points (ex. champ email). */
  children?: ReactNode;
  zIndexClass?: string;
  className?: string;
  closeLabel?: string;
  /** Vidéo panneau droit (défaut : rotation justice / brand / bureau). */
  visualVideo?: string;
};

/** Modal produit LexHub — panneau texte + visuel animé (bleu / orange). */
export function LexProductModal({
  open,
  onClose,
  tag,
  title,
  points = [],
  primaryLabel,
  primaryHref,
  onPrimary,
  secondaryLabel = "Plus tard",
  onSecondary,
  children,
  zIndexClass = "z-[70]",
  className,
  closeLabel = "Fermer",
  visualVideo,
}: LexProductModalProps) {
  const gemId = useId().replace(/:/g, "");
  const particlesRef = useRef<HTMLDivElement>(null);
  const videoSrc = useMemo(() => {
    if (visualVideo) return visualVideo;
    const i = Math.abs(Array.from(tag + title).reduce((a, c) => a + c.charCodeAt(0), 0)) % POPUP_VIDEOS.length;
    return POPUP_VIDEOS[i]!;
  }, [visualVideo, tag, title]);

  useEffect(() => {
    if (!open || !particlesRef.current) return;
    const el = particlesRef.current;
    el.innerHTML = "";
    const colors = ["#5a8bff", "#ff8a2d", "#3b5cde", "#ffb27a"];
    for (let i = 0; i < 22; i++) {
      const p = document.createElement("span");
      p.style.left = `${Math.random() * 100}%`;
      p.style.background = colors[Math.floor(Math.random() * colors.length)]!;
      p.style.animationDuration = `${6 + Math.random() * 6}s`;
      p.style.animationDelay = `${Math.random() * 8}s`;
      const size = `${2 + Math.random() * 3}px`;
      p.style.width = size;
      p.style.height = size;
      el.appendChild(p);
    }
  }, [open]);

  if (!open) return null;

  function handleSecondary() {
    (onSecondary || onClose)();
  }

  const primaryBtn = (
    <button
      type="button"
      className="lex-btn-primary"
      onClick={() => {
        if (onPrimary) onPrimary();
        else onClose();
      }}
    >
      {primaryLabel}
    </button>
  );

  return (
    <div
      className={cn("fixed inset-0 flex items-end justify-center p-0 sm:items-center sm:p-4", zIndexClass)}
      role="dialog"
      aria-modal
      aria-labelledby={`lex-modal-title-${gemId}`}
    >
      <button type="button" className="absolute inset-0 bg-black/55" aria-label={closeLabel} onClick={onClose} />
      <div className={cn("lex-modal relative z-[1] w-full sm:w-auto", className)}>
        <button
          type="button"
          className="lex-close lex-close--modal"
          onClick={onClose}
          aria-label={closeLabel}
        >
          ✕
        </button>
        <div className="lex-text">
          <span className="lex-tag">{tag}</span>
          <h2 id={`lex-modal-title-${gemId}`} className="lex-title">
            {title}
          </h2>

          {points.length > 0 ? (
            <div className="lex-points">
              {points.map((pt) => (
                <div key={pt} className="lex-point">
                  <Check className="h-[18px] w-[18px] shrink-0" strokeWidth={2.5} />
                  <span>{pt}</span>
                </div>
              ))}
            </div>
          ) : null}

          {children}

          <div className="lex-actions">
            {primaryHref ? (
              <Link href={primaryHref} className="lex-btn-primary" onClick={onClose}>
                {primaryLabel}
              </Link>
            ) : (
              primaryBtn
            )}
            <button type="button" className="lex-btn-secondary" onClick={handleSecondary}>
              {secondaryLabel}
            </button>
          </div>
        </div>

        <div className="lex-visual" aria-hidden>
          <video
            className="lex-visual-video"
            src={videoSrc}
            muted
            playsInline
            autoPlay
            loop
            preload="metadata"
          />
          <div className="lex-visual-scrim" />
          <div className="lex-blob lex-blob-blue" />
          <div className="lex-blob lex-blob-orange" />
          <div className="lex-particles" ref={particlesRef} />
          <div className="lex-orbit">
            <div className="lex-ring">
              <div className="lex-ring-2" />
            </div>
            <div className="lex-ping" />
            <div className="lex-ping" />
            <div className="lex-ping" />
            <div className="lex-gem-wrap">
              <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <linearGradient id={`lexGemGrad-${gemId}`} x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#5a8bff" />
                    <stop offset="50%" stopColor="#3b5cde" />
                    <stop offset="100%" stopColor="#ff8a2d" />
                  </linearGradient>
                </defs>
                <polygon
                  points="50,4 90,32 76,90 24,90 10,32"
                  fill={`url(#lexGemGrad-${gemId})`}
                  stroke="#ffffff"
                  strokeOpacity="0.25"
                  strokeWidth="1.5"
                />
                <polygon points="50,4 90,32 50,50" fill="#ffffff" fillOpacity="0.18" />
                <polygon points="10,32 50,50 24,90" fill="#000000" fillOpacity="0.12" />
                <polygon points="50,50 90,32 76,90" fill="#000000" fillOpacity="0.2" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
