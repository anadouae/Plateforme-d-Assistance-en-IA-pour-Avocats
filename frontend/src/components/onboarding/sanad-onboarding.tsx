"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useLocaleStore, useTranslations } from "@/store/locale";
import { useAuthStore } from "@/store/auth";
import {
  formatTourStepIndex,
  resolveOnboardingSteps,
} from "@/lib/onboarding-steps";

type Props = {
  open: boolean;
  onComplete: () => void;
};

type Placement = "bottom" | "top" | "left" | "right" | "center";

type Hole = { top: number; left: number; width: number; height: number };

function clamp(n: number, min: number, max: number) {
  return Math.min(max, Math.max(min, n));
}

function pickPlacement(rect: DOMRect): Placement {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  // Dock vertical gauche → bulle à droite
  if (rect.right < 120 && rect.width < 100) return "right";
  // Dock bas (mobile) → bulle au-dessus
  if (rect.top > vh * 0.72) return "top";
  // Topbar droite → bulle en dessous, un peu à gauche
  if (rect.top < 90 && rect.left > vw * 0.45) return "bottom";
  const spaceRight = vw - rect.right;
  const spaceLeft = rect.left;
  const spaceBelow = vh - rect.bottom;
  if (spaceRight >= 300) return "right";
  if (spaceBelow >= 220) return "bottom";
  if (spaceLeft >= 300) return "left";
  return "top";
}

export function SanadOnboarding({ open, onComplete }: Props) {
  const t = useTranslations().app.onboarding;
  const locale = useLocaleStore((s) => s.locale);
  const rtl = locale === "ar";
  const role = useAuthStore((s) => s.user?.role);
  const reduceMotion = useReducedMotion();
  const [index, setIndex] = useState(0);
  const [hole, setHole] = useState<Hole | null>(null);
  const [placement, setPlacement] = useState<Placement>("center");
  const [cardPos, setCardPos] = useState<{ top: number; left: number } | null>(null);
  const [arrowShift, setArrowShift] = useState(0);
  const [targetEl, setTargetEl] = useState<HTMLElement | null>(null);
  const cardRef = useRef<HTMLDivElement | null>(null);

  const steps = useMemo(() => resolveOnboardingSteps(locale, role), [locale, role]);
  const step = steps[index];
  const isLast = index >= steps.length - 1;

  const spring = reduceMotion
    ? { duration: 0 }
    : { type: "spring" as const, stiffness: 320, damping: 32, mass: 0.7 };

  const measure = useCallback(() => {
    if (!step) {
      setHole(null);
      setTargetEl(null);
      setPlacement("center");
      return true;
    }
    if (!step.target) {
      setHole(null);
      setTargetEl(null);
      setPlacement("center");
      return true;
    }
    const el = document.querySelector(step.target) as HTMLElement | null;
    if (!el) {
      setHole(null);
      setTargetEl(null);
      return false;
    }
    const style = window.getComputedStyle(el);
    if (style.display === "none" || style.visibility === "hidden" || style.opacity === "0") {
      setHole(null);
      setTargetEl(null);
      return false;
    }
    el.scrollIntoView({
      block: "nearest",
      inline: "nearest",
      behavior: reduceMotion ? "auto" : "smooth",
    });
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;

    const pad = 8;
    const nextHole: Hole = {
      top: clamp(r.top - pad, 4, window.innerHeight - 28),
      left: clamp(r.left - pad, 4, window.innerWidth - 28),
      width: clamp(r.width + pad * 2, 32, window.innerWidth - 8),
      height: clamp(r.height + pad * 2, 32, window.innerHeight - 8),
    };
    setHole(nextHole);
    setPlacement(pickPlacement(r));
    setTargetEl(el);
    return true;
  }, [step, reduceMotion]);

  // Élève la cible au-dessus du voile
  useEffect(() => {
    if (!open || !targetEl) return;
    const prev = {
      z: targetEl.style.zIndex,
      pos: targetEl.style.position,
      pe: targetEl.style.pointerEvents,
    };
    const computed = window.getComputedStyle(targetEl).position;
    if (computed === "static") targetEl.style.position = "relative";
    targetEl.style.zIndex = "100002";
    targetEl.style.pointerEvents = "auto";
    targetEl.classList.add("sanad-tour-target");
    return () => {
      targetEl.style.zIndex = prev.z;
      targetEl.style.position = prev.pos;
      targetEl.style.pointerEvents = prev.pe;
      targetEl.classList.remove("sanad-tour-target");
    };
  }, [open, targetEl]);

  useEffect(() => {
    if (!open || !step) return;
    let tries = 0;
    let tmr = 0;
    const tick = () => {
      const ok = measure();
      if (ok) return;
      tries += 1;
      if (tries >= 8) {
        // Cible introuvable → étape suivante (évite guide bloqué)
        if (index < steps.length - 1) setIndex((i) => i + 1);
        else onComplete();
        return;
      }
      tmr = window.setTimeout(tick, 160);
    };
    tmr = window.setTimeout(tick, 60);
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    return () => {
      window.clearTimeout(tmr);
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
    };
  }, [open, step, measure, index, steps.length, onComplete]);

  // Positionne la carte après mesure (hauteur réelle)
  useLayoutEffect(() => {
    if (!open) return;
    const cardW = Math.min(300, window.innerWidth - 28);
    const cardH = cardRef.current?.offsetHeight || 200;
    const gap = 14;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    if (!hole || placement === "center") {
      setCardPos({
        top: Math.max(16, (vh - cardH) / 2),
        left: Math.max(14, (vw - cardW) / 2),
      });
      setArrowShift(0);
      return;
    }

    let top = hole.top + hole.height + gap;
    let left = hole.left + hole.width / 2 - cardW / 2;

    if (placement === "top") {
      top = hole.top - gap - cardH;
      left = hole.left + hole.width / 2 - cardW / 2;
    } else if (placement === "right") {
      top = hole.top + hole.height / 2 - cardH / 2;
      left = hole.left + hole.width + gap;
    } else if (placement === "left") {
      top = hole.top + hole.height / 2 - cardH / 2;
      left = hole.left - gap - cardW;
    } else if (placement === "bottom") {
      top = hole.top + hole.height + gap;
      left = hole.left + hole.width / 2 - cardW / 2;
    }

    top = clamp(top, 12, vh - cardH - 12);
    left = clamp(left, 12, vw - cardW - 12);
    setCardPos({ top, left });

    // Flèche alignée sur le centre de la cible
    const holeCx = hole.left + hole.width / 2;
    const holeCy = hole.top + hole.height / 2;
    if (placement === "bottom" || placement === "top") {
      setArrowShift(clamp(holeCx - left - cardW / 2, -cardW / 2 + 28, cardW / 2 - 28));
    } else {
      setArrowShift(clamp(holeCy - top - 48, 28, cardH - 40));
    }
  }, [open, hole, placement, index, step?.id]);

  useEffect(() => {
    if (open) setIndex(0);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onComplete();
      } else if (e.key === "ArrowRight" || e.key === "Enter") {
        e.preventDefault();
        if (isLast) onComplete();
        else setIndex((i) => i + 1);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        setIndex((i) => Math.max(0, i - 1));
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onComplete, isLast]);

  if (!open || !step) return null;

  const arrowClass =
    placement === "bottom"
      ? "sanad-tour__arrow sanad-tour__arrow--up"
      : placement === "top"
        ? "sanad-tour__arrow sanad-tour__arrow--down"
        : placement === "left"
          ? "sanad-tour__arrow sanad-tour__arrow--right"
          : placement === "right"
            ? "sanad-tour__arrow sanad-tour__arrow--left"
            : "";

  const arrowStyle =
    placement === "bottom" || placement === "top"
      ? { left: `calc(50% + ${arrowShift}px)` }
      : placement === "left" || placement === "right"
        ? { top: arrowShift }
        : undefined;

  return (
    <AnimatePresence>
      <motion.div
        className="sanad-tour"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: reduceMotion ? 0 : 0.22 }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="sanad-tour-title"
        dir={rtl ? "rtl" : "ltr"}
      >
        <div className="sanad-tour__veil" onClick={onComplete} aria-hidden />

        {hole ? (
          <motion.div
            className="sanad-tour__hole"
            initial={false}
            animate={{
              top: hole.top,
              left: hole.left,
              width: hole.width,
              height: hole.height,
            }}
            transition={spring}
          />
        ) : (
          <div className="sanad-tour__dim" aria-hidden />
        )}

        <motion.div
          ref={cardRef}
          key={step.id}
          className="sanad-tour__card"
          style={
            cardPos
              ? { top: cardPos.top, left: cardPos.left }
              : { top: "50%", left: "50%", transform: "translate(-50%, -50%)" }
          }
          initial={reduceMotion ? false : { opacity: 0, y: 8, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: -4, scale: 0.99 }}
          transition={spring}
        >
          {hole && arrowClass ? (
            <span className={arrowClass} style={arrowStyle} aria-hidden />
          ) : null}

          <div className="sanad-tour__progress">
            <span>{formatTourStepIndex(index + 1, steps.length, locale)}</span>
            <div className="sanad-tour__bar" aria-hidden>
              <motion.i
                initial={false}
                animate={{ width: `${((index + 1) / steps.length) * 100}%` }}
                transition={spring}
              />
            </div>
          </div>

          <h2 id="sanad-tour-title">{step.title}</h2>
          <p>{step.body}</p>

          <div className="sanad-tour__actions">
            <button type="button" className="sanad-tour__ghost" onClick={onComplete}>
              {t.skip}
            </button>
            <div className="sanad-tour__nav">
              {index > 0 ? (
                <button
                  type="button"
                  className="sanad-tour__ghost"
                  onClick={() => setIndex((i) => Math.max(0, i - 1))}
                >
                  {t.back}
                </button>
              ) : null}
              <button
                type="button"
                className="sanad-tour__primary"
                onClick={() => {
                  if (isLast) onComplete();
                  else setIndex((i) => i + 1);
                }}
              >
                {isLast ? t.finish : t.next}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

/** Alias marque LexHub (même composant). */
export const LexHubOnboarding = SanadOnboarding;
