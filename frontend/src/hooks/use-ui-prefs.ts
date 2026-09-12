"use client";

import { useCallback, useEffect, useState } from "react";

const DENSITY_KEY = "lexhub-ui-density";
const THEME_KEY = "lexhub-ui-theme";
const FOCUS_EVENT = "lexhub-focus-mode";

export type UiDensity = "comfortable" | "compact";
export type UiTheme = "light" | "dark";

export function getUiDensity(): UiDensity {
  if (typeof window === "undefined") return "comfortable";
  return localStorage.getItem(DENSITY_KEY) === "compact" ? "compact" : "comfortable";
}

export function setUiDensity(d: UiDensity) {
  localStorage.setItem(DENSITY_KEY, d);
  document.documentElement.dataset.density = d;
  window.dispatchEvent(new Event("lexhub-density"));
}

export function useUiDensity() {
  const [density, setDensity] = useState<UiDensity>("comfortable");
  useEffect(() => {
    setDensity(getUiDensity());
    document.documentElement.dataset.density = getUiDensity();
    const on = () => setDensity(getUiDensity());
    window.addEventListener("lexhub-density", on);
    return () => window.removeEventListener("lexhub-density", on);
  }, []);
  const toggle = useCallback(() => {
    const next = getUiDensity() === "compact" ? "comfortable" : "compact";
    setUiDensity(next);
    setDensity(next);
  }, []);
  return { density, setDensity: (d: UiDensity) => { setUiDensity(d); setDensity(d); }, toggle };
}

export function getUiTheme(): UiTheme {
  if (typeof window === "undefined") return "light";
  return localStorage.getItem(THEME_KEY) === "dark" ? "dark" : "light";
}

export function setUiTheme(t: UiTheme) {
  localStorage.setItem(THEME_KEY, t);
  document.documentElement.dataset.theme = t;
  window.dispatchEvent(new Event("lexhub-theme"));
}

export function useUiTheme() {
  const [theme, setTheme] = useState<UiTheme>("light");
  useEffect(() => {
    setTheme(getUiTheme());
    document.documentElement.dataset.theme = getUiTheme();
    const on = () => setTheme(getUiTheme());
    window.addEventListener("lexhub-theme", on);
    return () => window.removeEventListener("lexhub-theme", on);
  }, []);
  const toggle = useCallback(() => {
    const next: UiTheme = getUiTheme() === "dark" ? "light" : "dark";
    setUiTheme(next);
    setTheme(next);
  }, []);
  return {
    theme,
    setTheme: (t: UiTheme) => {
      setUiTheme(t);
      setTheme(t);
    },
    toggle,
  };
}

export function setFocusMode(on: boolean) {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("lexhub-focus", on);
  window.dispatchEvent(new CustomEvent(FOCUS_EVENT, { detail: { on } }));
}

export function useFocusModeListener(cb: (on: boolean) => void) {
  useEffect(() => {
    const on = (e: Event) => cb(!!(e as CustomEvent).detail?.on);
    window.addEventListener(FOCUS_EVENT, on);
    return () => window.removeEventListener(FOCUS_EVENT, on);
  }, [cb]);
}
