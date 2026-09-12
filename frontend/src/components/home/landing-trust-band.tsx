"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";

function useCountUp(target: number, active: boolean, duration = 1200) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!active) return;
    const start = performance.now();
    let raf = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      setN(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active, duration]);
  return n;
}

export function LandingTrustBand({ ar }: { ar: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(false);
  const reduce = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e?.isIntersecting) setActive(true);
      },
      { threshold: 0.3 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const cabinets = useCountUp(4, active || !!reduce);
  const secure = useCountUp(100, active || !!reduce);

  const items = [
    {
      value: ar ? "تجربة" : "Essai",
      suffix: "",
      label: ar ? "قابل للتعديل حسب العرض" : "Durée selon l’offre",
    },
    {
      value: reduce ? "4" : `${cabinets}`,
      suffix: "",
      label: ar ? "خطط مرنة" : "Plans flexibles",
    },
    {
      value: reduce ? "100%" : `${secure}%`,
      suffix: "",
      label: ar ? "مصمم للمغرب" : "Conçu pour le Maroc",
    },
  ];

  return (
    <section
      ref={ref}
      className="relative z-20 border-y border-[rgba(140,170,255,0.12)] bg-[#0A1228]/95 px-6 py-10 backdrop-blur-sm sm:px-8"
    >
      <div className="mx-auto grid max-w-[900px] gap-8 sm:grid-cols-3">
        {items.map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 16 }}
            animate={active ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: i * 0.12, duration: 0.5 }}
            className="text-center"
          >
            <p className="font-display text-3xl font-semibold text-[#FFE6C2]">
              {item.value}
              {item.suffix ? (
                <span className="text-lg font-normal text-[#A8C0FF]">{item.suffix}</span>
              ) : null}
            </p>
            <p className="mt-1 text-xs uppercase tracking-[0.14em] text-[#A8B6D4]">{item.label}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
