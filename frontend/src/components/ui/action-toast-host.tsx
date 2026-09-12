"use client";

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, XCircle } from "lucide-react";
import { useActionToast } from "@/store/action-toast";

export function ActionToastHost() {
  const toasts = useActionToast((s) => s.toasts);
  const dismiss = useActionToast((s) => s.dismiss);

  return (
    <div className="action-toast-stack" aria-live="polite" aria-relevant="additions">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            className={`action-toast action-toast--${t.tone}`}
            initial={{ opacity: 0, y: 18, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.96 }}
            transition={{ type: "spring", stiffness: 420, damping: 28 }}
            role="status"
            onClick={() => dismiss(t.id)}
          >
            {t.tone === "success" ? (
              <CheckCircle2 className="action-toast__icon" size={18} />
            ) : t.tone === "error" ? (
              <XCircle className="action-toast__icon" size={18} />
            ) : (
              <Info className="action-toast__icon" size={18} />
            )}
            <span className="action-toast__msg">{t.message}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
