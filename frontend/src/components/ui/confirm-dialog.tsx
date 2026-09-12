"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, FileText, FolderOpen, ShieldAlert, Trash2 } from "lucide-react";
import { useLocaleStore } from "@/store/locale";

export type ConfirmOptions = {
  title: string;
  description?: string;
  /** Contenu enrichi (ex. aperçu dossier) entre description et type-to-confirm */
  preview?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "default" | "danger";
  /** Pour suppressions : taper supprimer / delete / حذف */
  requireDeletePhrase?: boolean;
  /** Icône animée vers la poubelle */
  deleteVisual?: "folder" | "document" | "generic";
};

type Pending = ConfirmOptions & {
  resolve: (ok: boolean) => void;
};

type ConfirmApi = (options: ConfirmOptions) => Promise<boolean>;

const ConfirmContext = createContext<ConfirmApi | null>(null);

const DELETE_PHRASES = new Set(["supprimer", "delete", "حذف"]);

function phraseOk(value: string) {
  return DELETE_PHRASES.has(value.trim().toLowerCase());
}

function DeleteFlyAnim({ visual }: { visual: "folder" | "document" | "generic" }) {
  const Icon = visual === "document" ? FileText : FolderOpen;
  return (
    <div className="sanad-confirm-fly" aria-hidden>
      <motion.div
        className="sanad-confirm-fly__item"
        initial={{ x: -36, y: 8, opacity: 0, scale: 0.7, rotate: -12 }}
        animate={{
          x: [ -36, 8, 42 ],
          y: [ 8, -18, 10 ],
          opacity: [0, 1, 0],
          scale: [0.7, 1.05, 0.55],
          rotate: [-12, 0, 18],
        }}
        transition={{ duration: 1.35, repeat: Infinity, ease: "easeInOut", repeatDelay: 0.35 }}
      >
        <Icon size={22} strokeWidth={1.75} />
      </motion.div>
      <motion.div
        className="sanad-confirm-fly__trash"
        animate={{ scale: [1, 1.08, 1], rotate: [0, -6, 0] }}
        transition={{ duration: 1.35, repeat: Infinity, ease: "easeInOut", repeatDelay: 0.35 }}
      >
        <Trash2 size={26} strokeWidth={1.75} />
      </motion.div>
    </div>
  );
}

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [pending, setPending] = useState<Pending | null>(null);
  const [typed, setTyped] = useState("");
  const [mounted, setMounted] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const titleId = useId();
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";

  useEffect(() => {
    setMounted(true);
  }, []);

  const confirm = useCallback<ConfirmApi>((options) => {
    return new Promise<boolean>((resolve) => {
      setTyped("");
      setPending({ ...options, resolve });
    });
  }, []);

  useEffect(() => {
    if (!pending) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        pending.resolve(false);
        setPending(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pending]);

  useEffect(() => {
    if (pending?.requireDeletePhrase) {
      const t = window.setTimeout(() => inputRef.current?.focus(), 80);
      return () => window.clearTimeout(t);
    }
  }, [pending]);

  function close(ok: boolean) {
    pending?.resolve(ok);
    setPending(null);
    setTyped("");
  }

  const canConfirm = !pending?.requireDeletePhrase || phraseOk(typed);
  const isDelete = !!(pending?.requireDeletePhrase || pending?.tone === "danger");

  const defaults = {
    cancel: ar ? "إلغاء" : "Annuler",
    ok: ar ? "تأكيد" : "Confirmer",
    delete: ar ? "حذف نهائياً" : "Supprimer",
    typeHint: ar
      ? "اكتب حذف أو delete أو supprimer للتأكيد"
      : "Tapez supprimer ou delete pour confirmer",
  };

  const modal = (
    <AnimatePresence>
      {pending ? (
        <motion.div
          className="sanad-confirm-root"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <motion.button
            type="button"
            className="sanad-confirm-backdrop"
            aria-label={defaults.cancel}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => close(false)}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className={`sanad-confirm-card${isDelete ? " sanad-confirm-card--danger" : ""}`}
            initial={{ opacity: 0, y: 28, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 380, damping: 28 }}
          >
            <div className="sanad-confirm-glow" aria-hidden />

            <button
              type="button"
              className="sanad-confirm-close"
              aria-label={ar ? "إغلاق" : "Fermer"}
              onClick={() => close(false)}
            >
              ✕
            </button>

            {pending.requireDeletePhrase || pending.deleteVisual ? (
              <DeleteFlyAnim visual={pending.deleteVisual || "folder"} />
            ) : (
              <div className="sanad-confirm-icon" aria-hidden>
                {isDelete ? <ShieldAlert size={22} /> : <AlertTriangle size={22} />}
              </div>
            )}

            <h2 id={titleId} className="sanad-confirm-title">
              {pending.title}
            </h2>
            {pending.description ? (
              <p className="sanad-confirm-desc">{pending.description}</p>
            ) : null}

            {pending.preview ? (
              <div className="sanad-confirm-preview">{pending.preview}</div>
            ) : null}

            {pending.requireDeletePhrase ? (
              <label className="sanad-confirm-type">
                <span>{defaults.typeHint}</span>
                <input
                  ref={inputRef}
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder={ar ? "حذف" : "supprimer"}
                  autoComplete="off"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && canConfirm) close(true);
                  }}
                />
              </label>
            ) : null}

            <div className="sanad-confirm-actions">
              <button
                type="button"
                className="sanad-confirm-btn sanad-confirm-btn--ghost"
                onClick={() => close(false)}
              >
                {pending.cancelLabel || defaults.cancel}
              </button>
              <button
                type="button"
                className={`sanad-confirm-btn${
                  isDelete ? " sanad-confirm-btn--danger" : " sanad-confirm-btn--primary"
                }`}
                disabled={!canConfirm}
                onClick={() => close(true)}
              >
                {pending.confirmLabel ||
                  (pending.requireDeletePhrase ? defaults.delete : defaults.ok)}
              </button>
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {mounted ? createPortal(modal, document.body) : null}
    </ConfirmContext.Provider>
  );
}

export function useConfirm(): ConfirmApi {
  const ctx = useContext(ConfirmContext);
  if (!ctx) {
    throw new Error("useConfirm must be used within ConfirmProvider");
  }
  return ctx;
}
