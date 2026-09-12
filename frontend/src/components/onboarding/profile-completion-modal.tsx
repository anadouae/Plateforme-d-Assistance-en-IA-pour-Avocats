"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { canManageTeam } from "@/lib/roles";

const SKIP_KEY = "lexhub_profile_prompt_skip";

/** Popup post-connexion : téléphone + nom AR / logo cabinet. */
export function ProfileCompletionModal() {
  const ar = useClientLocale() === "ar";
  const user = useAuthStore((s) => s.user);
  const isAdmin = canManageTeam(user?.role);
  const [open, setOpen] = useState(false);
  const [phone, setPhone] = useState("");
  const [nameAr, setNameAr] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!user || user.role === "admin_webvoice") return;
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(SKIP_KEY) === "1") return;
    const needsPhone = !user.phone;
    const needsLogo = isAdmin && !user.cabinet_has_logo;
    const needsNameAr = isAdmin && !user.cabinet_name_ar;
    if (needsPhone || needsLogo || needsNameAr) {
      setOpen(true);
      setPhone(user.phone || "");
      setNameAr(user.cabinet_name_ar || "");
    }
  }, [user, isAdmin]);

  if (!open) return null;

  async function save() {
    setBusy(true);
    setErr("");
    setMsg("");
    try {
      if (phone.trim()) {
        await api.updateProfileNames({ phone: phone.trim() });
      }
      if (isAdmin && nameAr.trim()) {
        await api.updateCabinetSettings({ name_ar: nameAr.trim() });
      }
      const me = await api.getMe();
      useAuthStore.setState({ user: me });
      setMsg(ar ? "تم الحفظ." : "Enregistré.");
      sessionStorage.setItem(SKIP_KEY, "1");
      setOpen(false);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Erreur");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[9995] flex items-center justify-center bg-[#0B1A4D]/45 p-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <h2 className="text-xl font-semibold text-[#0B1A4D]">
          {ar ? "أكملوا ملفكم" : "Complétez votre profil"}
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          {ar
            ? "رقم الهاتف واسم المكتب بالعربية يحسّنان التواصل وترويسة المرافعات."
            : "Téléphone et nom arabe du cabinet améliorent le contact et l’en-tête des plaidoiries."}
        </p>
        <div className="mt-4 space-y-3">
          <Input
            label={ar ? "الهاتف" : "Téléphone"}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+212 6…"
          />
          {isAdmin ? (
            <>
              <Input
                label={ar ? "اسم المكتب بالعربية" : "Nom du cabinet (arabe)"}
                value={nameAr}
                dir="rtl"
                onChange={(e) => setNameAr(e.target.value)}
              />
              {!user?.cabinet_has_logo ? (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => window.location.assign("/settings#cabinet")}
                >
                  {ar ? "رفع شعار المكتب" : "Uploader le logo du cabinet"}
                </Button>
              ) : null}
            </>
          ) : null}
        </div>
        {msg ? <p className="mt-2 text-sm text-emerald-700">{msg}</p> : null}
        {err ? <p className="mt-2 text-sm text-red-600">{err}</p> : null}
        <div className="mt-5 flex flex-wrap gap-2">
          <Button type="button" disabled={busy} onClick={() => void save()}>
            {busy ? "…" : ar ? "حفظ" : "Enregistrer"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              sessionStorage.setItem(SKIP_KEY, "1");
              setOpen(false);
            }}
          >
            {ar ? "لاحقاً" : "Plus tard"}
          </Button>
        </div>
      </div>
    </div>
  );
}
