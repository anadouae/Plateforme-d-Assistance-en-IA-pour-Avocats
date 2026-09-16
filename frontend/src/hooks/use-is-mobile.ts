"use client";

import { useEffect, useState } from "react";

/** True sous ~880px (dock mobile LexHub). SSR = false. */
export function useIsMobile(breakpoint = 880): boolean {
  const [mobile, setMobile] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${breakpoint}px)`);
    const apply = () => setMobile(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, [breakpoint]);

  return mobile;
}
