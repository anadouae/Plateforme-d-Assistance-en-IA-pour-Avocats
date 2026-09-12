"use client";

import { Moon, Sun } from "lucide-react";
import { useUiTheme } from "@/hooks/use-ui-prefs";
import { useClientLocale } from "@/store/locale";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggle } = useUiTheme();
  const ar = useClientLocale() === "ar";
  const dark = theme === "dark";

  return (
    <button
      type="button"
      className={className || "topbar-ico"}
      onClick={toggle}
      aria-label={
        dark
          ? ar
            ? "الوضع الفاتح"
            : "Passer au thème clair"
          : ar
            ? "الوضع الداكن"
            : "Passer au thème sombre"
      }
      title={dark ? (ar ? "فاتح" : "Thème clair") : ar ? "داكن" : "Thème sombre"}
    >
      {dark ? (
        <Sun className="h-[18px] w-[18px] topbar-ico__glyph" />
      ) : (
        <Moon className="h-[18px] w-[18px] topbar-ico__glyph" />
      )}
    </button>
  );
}
