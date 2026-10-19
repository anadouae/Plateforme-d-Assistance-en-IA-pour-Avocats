"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useRouter } from "next/navigation";
import { LogOut, User } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { useLocaleStore, useTranslations } from "@/store/locale";

function initials(name?: string | null) {
  if (!name) return "S";
  const p = name.trim().split(/\s+/).filter(Boolean);
  if (p.length === 1) return p[0].slice(0, 2).toUpperCase();
  return `${p[0][0]}${p[p.length - 1][0]}`.toUpperCase();
}

/**
 * Menu compte toujours visible (topbar) — Paramètres + Déconnexion.
 * Évite le dock-foot masqué en &lt; 880px et les menus coupés par overflow.
 */
export function UserAccountMenu({
  compact = false,
  hideSettings = false,
}: {
  compact?: boolean;
  /** Espace admin plateforme : pas de lien Paramètres cabinet. */
  hideSettings?: boolean;
}) {
  const { user, logout } = useAuthStore();
  const t = useTranslations().app;
  const router = useRouter();
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const isPlatformAdmin = user?.role === "admin_webvoice" || hideSettings;
  const [open, setOpen] = useState(false);
  const [box, setBox] = useState<{ top: number; right: number } | null>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const place = useCallback(() => {
    const btn = btnRef.current;
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    const menuW = 220;
    // Ancré sous le bouton, aligné à droite de l’avatar (toujours dans le viewport)
    let right = window.innerWidth - r.right;
    right = Math.max(8, Math.min(right, window.innerWidth - menuW - 8));
    const top = Math.min(r.bottom + 8, window.innerHeight - 120);
    setBox({ top, right });
  }, []);

  useEffect(() => {
    if (!open) return;
    place();
    function onDoc(e: MouseEvent) {
      const n = e.target as Node;
      if (btnRef.current?.contains(n) || menuRef.current?.contains(n)) return;
      setOpen(false);
    }
    function onRepo() {
      place();
    }
    document.addEventListener("mousedown", onDoc);
    window.addEventListener("resize", onRepo);
    window.addEventListener("scroll", onRepo, true);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      window.removeEventListener("resize", onRepo);
      window.removeEventListener("scroll", onRepo, true);
    };
  }, [open, place]);

  const menu =
    open && box
      ? createPortal(
          <div
            ref={menuRef}
            role="menu"
            dir={ar ? "rtl" : "ltr"}
            style={{
              position: "fixed",
              top: box.top,
              right: box.right,
              width: 220,
              background: "#fff",
              border: "1px solid var(--line, rgba(14,21,38,0.1))",
              borderRadius: 16,
              boxShadow: "0 20px 50px -18px rgba(14,21,38,0.35)",
              padding: "6px 0",
              zIndex: 100000,
            }}
          >
            <div
              style={{
                padding: "10px 14px 8px",
                borderBottom: "1px solid rgba(14,21,38,0.08)",
                marginBottom: 4,
              }}
            >
              <p
                style={{
                  margin: 0,
                  fontSize: 13,
                  fontWeight: 700,
                  color: "var(--ink, #0A1228)",
                }}
              >
                {user?.full_name || "LexHub"}
              </p>
              <p
                style={{
                  margin: "2px 0 0",
                  fontSize: 11,
                  color: "var(--ink-soft, #3B4459)",
                  wordBreak: "break-all",
                }}
              >
                {user?.email || ""}
              </p>
            </div>
            {!isPlatformAdmin ? (
              <button
                type="button"
                role="menuitem"
                className="btn-ghost"
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  justifyContent: ar ? "flex-end" : "flex-start",
                  flexDirection: ar ? "row-reverse" : "row",
                  border: "none",
                  borderRadius: 0,
                  padding: "11px 14px",
                  background: "transparent",
                  cursor: "pointer",
                  fontSize: 13.5,
                  fontWeight: 600,
                  color: "var(--ink, #0A1228)",
                }}
                onClick={() => {
                  setOpen(false);
                  router.push("/settings");
                }}
              >
                <User width={16} height={16} />
                {t.nav.settings}
              </button>
            ) : null}
            <button
              type="button"
              role="menuitem"
              className="btn-ghost"
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 10,
                justifyContent: ar ? "flex-end" : "flex-start",
                flexDirection: ar ? "row-reverse" : "row",
                border: "none",
                borderRadius: 0,
                padding: "11px 14px",
                background: "transparent",
                cursor: "pointer",
                fontSize: 13.5,
                fontWeight: 600,
                color: "#b91c1c",
              }}
              onClick={() => {
                setOpen(false);
                if (user?.must_set_password && !user?.auth_via_google) {
                  const ok = window.confirm(
                    ar
                      ? "لم تنشئوا كلمة مرور بعد. عند الخروج ستحتاجون رمزاً بالبريد للدخول. إنشاء كلمة المرور الآن؟\n\nموافق = البقاء وإنشاء لاحقاً من الشريط الأصفر\nإلغاء = الخروج الآن"
                      : "Vous n’avez pas encore de mot de passe. Après déconnexion, un code e-mail sera nécessaire. Créer le mot de passe maintenant ?\n\nOK = rester (utilisez le bandeau jaune)\nAnnuler = se déconnecter quand même",
                  );
                  if (ok) return;
                }
                logout();
                router.replace("/login");
              }}
            >
              <LogOut width={16} height={16} />
              {t.logout}
            </button>
          </div>,
          document.body,
        )
      : null;

  return (
    <>
      {!compact ? (
        <button
          type="button"
          onClick={() => {
            logout();
            router.replace("/login");
          }}
          aria-label={ar ? "تسجيل الخروج" : "Déconnexion"}
          title={ar ? "تسجيل الخروج" : "Déconnexion"}
          className="topbar-logout-btn"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            border: "1px solid rgba(185, 28, 28, 0.25)",
            background: "rgba(254, 242, 242, 0.95)",
            borderRadius: 999,
            padding: "8px 12px",
            cursor: "pointer",
            fontSize: 12.5,
            fontWeight: 700,
            color: "#b91c1c",
            boxShadow: "var(--shadow-sm, 0 8px 24px -12px rgba(14,21,38,0.18))",
          }}
        >
          <LogOut width={14} height={14} />
          {ar ? "خروج" : "Déconnexion"}
        </button>
      ) : null}
      <button
        ref={btnRef}
        type="button"
        className="topbar-account-btn"
        onClick={() => {
          setOpen((v) => {
            const next = !v;
            if (next) requestAnimationFrame(() => place());
            else setBox(null);
            return next;
          });
        }}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={ar ? "الحساب" : "Compte"}
        title={ar ? "الحساب" : "Compte"}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          border: "1px solid var(--line, rgba(14,21,38,0.1))",
          background: "rgba(255,255,255,0.85)",
          borderRadius: 999,
          padding: compact ? "4px" : "4px 10px 4px 4px",
          cursor: "pointer",
          boxShadow: "var(--shadow-sm, 0 8px 24px -12px rgba(14,21,38,0.18))",
          flexShrink: 0,
        }}
      >
        <span
          style={{
            width: compact ? 36 : 34,
            height: compact ? 36 : 34,
            borderRadius: "50%",
            background: "linear-gradient(155deg, var(--royal-700), var(--royal-900))",
            color: "#fff",
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 12,
            fontWeight: 700,
            fontFamily: "var(--font-fraunces), Georgia, serif",
          }}
        >
          {initials(user?.full_name)}
        </span>
        {!compact && (
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontSize: 12.5,
              fontWeight: 600,
              color: "var(--ink-soft, #3B4459)",
              paddingInlineEnd: 4,
            }}
          >
            <User width={14} height={14} />
            {ar ? "الحساب" : "Compte"}
          </span>
        )}
      </button>
      {menu}
    </>
  );
}
