"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell, CreditCard, CircleHelp, Search, Settings } from "lucide-react";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { api, type CabinetNotificationItem } from "@/lib/api";
import { canManageTeam } from "@/lib/roles";
import { useAuthStore } from "@/store/auth";
import { useClientLocale, useTranslations } from "@/store/locale";
import { cn } from "@/lib/utils";
import { useCabinetEvent } from "@/hooks/use-cabinet-realtime";
import { useIsMobile } from "@/hooks/use-is-mobile";

/**
 * Recherche ⌘K + Paramètres + cloche (notifs plaidoirie).
 */
export function TopbarActionIcons() {
  const t = useTranslations().app;
  const locale = useClientLocale();
  const ar = locale === "ar";
  const isMobile = useIsMobile();
  const role = useAuthStore((s) => s.user?.role);
  const manage = canManageTeam(role);
  const router = useRouter();
  const [unread, setUnread] = useState(0);
  const [items, setItems] = useState<CabinetNotificationItem[]>([]);
  const [open, setOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [mounted, setMounted] = useState(false);
  const bellBtnRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);
  const helpBtnRef = useRef<HTMLButtonElement | null>(null);
  const helpPanelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => setMounted(true), []);

  function openCommandPalette() {
    window.dispatchEvent(new Event("lexhub-open-cmdk"));
  }

  const refreshNotifs = useCallback(async () => {
    try {
      const [{ count }, list] = await Promise.all([
        api.getNotificationsUnreadCount(),
        api.getNotifications(false),
      ]);
      setUnread(count);
      setItems(list.slice(0, 20));
    } catch {
      /* silencieux */
    }
  }, []);

  useEffect(() => {
    void refreshNotifs();
    const id = window.setInterval(() => {
      void refreshNotifs();
    }, 60_000);
    const onFocus = () => {
      void refreshNotifs();
    };
    window.addEventListener("focus", onFocus);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("focus", onFocus);
    };
  }, [refreshNotifs]);

  const cabinetEvtBusy = useRef(false);
  useCabinetEvent(() => {
    if (cabinetEvtBusy.current) return;
    cabinetEvtBusy.current = true;
    void refreshNotifs().finally(() => {
      window.setTimeout(() => {
        cabinetEvtBusy.current = false;
      }, 2500);
    });
  });

  useEffect(() => {
    if (!open && !helpOpen) return;
    function onDoc(e: MouseEvent) {
      const n = e.target as Node;
      if (
        bellBtnRef.current?.contains(n) ||
        panelRef.current?.contains(n) ||
        helpBtnRef.current?.contains(n) ||
        helpPanelRef.current?.contains(n)
      ) {
        return;
      }
      setOpen(false);
      setHelpOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open, helpOpen]);

  async function openNotif(n: CabinetNotificationItem) {
    if (!n.read) {
      try {
        await api.markNotificationRead(n.id);
        setUnread((c) => Math.max(0, c - 1));
        setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, read: true } : x)));
      } catch {
        /* ignore */
      }
    }
    setOpen(false);
    router.push(n.href || "/redaction");
  }

  const notifPanel = open ? (
    <div
      ref={panelRef}
      className={cn("topbar-notif-panel", isMobile && "topbar-notif-panel--sheet")}
      role="menu"
      dir={ar ? "rtl" : "ltr"}
    >
      <div className="topbar-notif-panel__head">
        <span>{ar ? "الإشعارات" : "Notifications"}</span>
        <div className="flex flex-wrap gap-2">
          {unread > 0 ? (
            <button
              type="button"
              className="topbar-notif-panel__clear"
              onClick={() =>
                void api.markAllNotificationsRead().then(() => {
                  setUnread(0);
                  setItems((prev) => prev.map((x) => ({ ...x, read: true })));
                })
              }
            >
              {ar ? "علم الكل كمقروء" : "Tout lu"}
            </button>
          ) : null}
          {items.length > 0 ? (
            <button
              type="button"
              className="topbar-notif-panel__clear"
              onClick={() =>
                void api.deleteNotifications({ all: true }).then(() => {
                  setItems([]);
                  setUnread(0);
                  setSelected({});
                })
              }
            >
              {ar ? "حذف الكل" : "Tout supprimer"}
            </button>
          ) : null}
          {Object.values(selected).some(Boolean) ? (
            <button
              type="button"
              className="topbar-notif-panel__clear"
              onClick={() => {
                const ids = Object.entries(selected)
                  .filter(([, v]) => v)
                  .map(([id]) => id);
                void api.deleteNotifications({ ids }).then(() => {
                  setItems((prev) => prev.filter((x) => !ids.includes(x)));
                  setSelected({});
                  void refreshNotifs();
                });
              }}
            >
              {ar ? "حذف المحدد" : "Supprimer la sélection"}
            </button>
          ) : null}
        </div>
      </div>
      {items.length === 0 ? (
        <p className="topbar-notif-empty">
          {ar ? "لا إشعارات حالياً" : "Aucune notification"}
        </p>
      ) : (
        items.map((n) => (
          <div key={n.id} className="flex items-start gap-2 px-2">
            <input
              type="checkbox"
              className="mt-3"
              checked={Boolean(selected[n.id])}
              onChange={(e) =>
                setSelected((prev) => ({ ...prev, [n.id]: e.target.checked }))
              }
              aria-label={ar ? "تحديد" : "Sélectionner"}
            />
            <button
              type="button"
              className={cn("topbar-notif-item flex-1", !n.read && "topbar-notif-item--unread")}
              onClick={() => void openNotif(n)}
            >
              <strong>{n.title}</strong>
              {n.body ? <span>{n.body}</span> : null}
            </button>
          </div>
        ))
      )}
    </div>
  ) : null;

  const helpPanel = helpOpen ? (
    <div
      ref={helpPanelRef}
      className={cn("topbar-notif-panel", isMobile && "topbar-notif-panel--sheet")}
      role="menu"
      dir={ar ? "rtl" : "ltr"}
    >
      <div className="topbar-notif-panel__head">
        <span>{ar ? "مساعدة" : "Help"}</span>
      </div>
      <Link href="/aide" className="topbar-notif-item" onClick={() => setHelpOpen(false)}>
        <strong>{ar ? "مركز المساعدة" : "Help Center"}</strong>
        <span>{ar ? "أدلة وموضوعات LexHub" : "Guides et sujets LexHub"}</span>
      </Link>
      <Link href="/contact" className="topbar-notif-item" onClick={() => setHelpOpen(false)}>
        <strong>{ar ? "تحدثوا معنا" : "Chat with us"}</strong>
        <span>{ar ? "تواصل مع الدعم" : "Contacter le support"}</span>
      </Link>
    </div>
  ) : null;

  return (
    <div className="topbar-actions" style={{ display: "flex", alignItems: "center", gap: isMobile ? 6 : 10 }}>
      <button
        type="button"
        className="topbar-ico"
        aria-label={ar ? "بحث (Ctrl+K)" : "Recherche (Ctrl+K)"}
        title={ar ? "بحث ⌘K" : "Recherche ⌘K"}
        onClick={openCommandPalette}
      >
        <Search className="h-[18px] w-[18px] topbar-ico__glyph" />
      </button>

      <div className="topbar-bell-wrap">
        <button
          ref={bellBtnRef}
          type="button"
          className={cn(
            "topbar-ico",
            unread > 0 && "topbar-ico--alert",
          )}
          aria-label={ar ? "الإشعارات" : "Notifications"}
          title={ar ? "الإشعارات" : "Notifications"}
          data-tour-id="notifications"
          aria-expanded={open}
          onClick={() => {
            setHelpOpen(false);
            setOpen((v) => !v);
          }}
        >
          <Bell className="h-[18px] w-[18px] topbar-ico__glyph" />
          {unread > 0 ? (
            <span className="topbar-ico__badge" aria-hidden>
              {unread > 9 ? "9+" : unread}
            </span>
          ) : null}
        </button>
      </div>

      {manage ? (
        <Link
          href="/settings#abonnement"
          className="topbar-ico"
          aria-label={ar ? "اشتراكي" : "Mon abonnement"}
          title={ar ? "اشتراكي" : "Mon abonnement"}
        >
          <CreditCard className="h-[18px] w-[18px] topbar-ico__glyph" />
        </Link>
      ) : null}

      <div className="topbar-bell-wrap">
        <button
          ref={helpBtnRef}
          type="button"
          className="topbar-ico topbar-ico--help"
          aria-label={ar ? "مساعدة" : "Aide"}
          title={ar ? "مساعدة" : "Aide"}
          aria-expanded={helpOpen}
          onClick={() => {
            setOpen(false);
            setHelpOpen((v) => !v);
          }}
        >
          <CircleHelp className="h-[18px] w-[18px] topbar-ico__glyph" />
        </button>
      </div>

      <ThemeToggle className="topbar-ico topbar-ico--theme" />

      <Link
        href="/settings"
        className="topbar-ico topbar-ico--settings"
        aria-label={t.nav.settings}
        title={t.nav.settings}
        data-tour-id="settings"
      >
        <Settings className="h-[18px] w-[18px] topbar-ico__glyph" />
      </Link>

      {mounted && open
        ? createPortal(
            <>
              {isMobile ? (
                <button
                  type="button"
                  className="topbar-sheet-backdrop"
                  aria-label={ar ? "إغلاق" : "Fermer"}
                  onClick={() => setOpen(false)}
                />
              ) : null}
              {notifPanel}
            </>,
            document.body,
          )
        : null}
      {mounted && helpOpen
        ? createPortal(
            <>
              {isMobile ? (
                <button
                  type="button"
                  className="topbar-sheet-backdrop"
                  aria-label={ar ? "إغلاق" : "Fermer"}
                  onClick={() => setHelpOpen(false)}
                />
              ) : null}
              {helpPanel}
            </>,
            document.body,
          )
        : null}
    </div>
  );
}
