"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { canManageTeam } from "@/lib/roles";

const SKIP_KEY = "lexhub_profile_prompt_skip";

/**
 * Rappel non bloquant après inscription minimale.
 * L'utilisateur peut toujours passer (« Plus tard ») et utiliser LexHub.
 * Les infos cabinet améliorent l'en-tête Word — rappelées aussi en bannière / à l'export.
 */
export function ProfileCompletionModal() {
  const router = useRouter();
  const ar = useClientLocale() === "ar";
  const user = useAuthStore((s) => s.user);
  const isAdmin = canManageTeam(user?.role);
  const [open, setOpen] = useState(false);
  const [cabinetName, setCabinetName] = useState("");
  const [city, setCity] = useState("");
  const [barreau, setBarreau] = useState("");
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const incomplete = user ? user.cabinet_profile_complete === false : false;

  useEffect(() => {
    if (!user || user.role === "admin_webvoice") return;
    if (typeof window === "undefined") return;
    // Jamais bloquant : si l'utilisateur a dit « Plus tard », on ne réouvre pas
    if (sessionStorage.getItem(SKIP_KEY) === "1") return;

    if (isAdmin && incomplete) {
      setOpen(true);
      const placeholder = "À compléter";
      const rawName = user.cabinet_name || "";
      setCabinetName(
        rawName.toLowerCase().startsWith("cabinet temporaire") ? "" : rawName,
      );
      setCity(user.cabinet_city === placeholder ? "" : user.cabinet_city || "");
      setBarreau(user.cabinet_barreau === placeholder ? "" : user.cabinet_barreau || "");
      setAddress(user.cabinet_address === placeholder ? "" : user.cabinet_address || "");
      setPhone(user.phone || "");
      return;
    }

    if (!user.phone || (isAdmin && !user.cabinet_has_logo)) {
      setOpen(true);
      setPhone(user.phone || "");
    }
  }, [user, isAdmin, incomplete]);

  function dismiss() {
    sessionStorage.setItem(SKIP_KEY, "1");
    setOpen(false);
  }

  function goToSettings() {
    sessionStorage.setItem(SKIP_KEY, "1");
    setOpen(false);
    router.push("/settings#cabinet");
  }

  if (!open) return null;

  async function save() {
    setBusy(true);
    setErr("");
    setMsg("");
    try {
      if (isAdmin && incomplete) {
        const payload: Record<string, string> = {};
        if (cabinetName.trim().length >= 2) payload.name = cabinetName.trim();
        if (city.trim().length >= 2) payload.city = city.trim();
        if (barreau.trim().length >= 2) payload.barreau = barreau.trim();
        if (address.trim().length >= 5) payload.address = address.trim();
        if (Object.keys(payload).length === 0) {
          setErr(
            ar
              ? "أدخلوا معلومة واحدة على الأقل، أو اختاروا «لاحقاً»."
              : "Saisissez au moins une info, ou choisissez « Plus tard ».",
          );
          setBusy(false);
          return;
        }
        await api.updateCabinetSettings(payload);
      }
      if (phone.trim()) {
        await api.updateProfileNames({ phone: phone.trim() });
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
    <div className="fixed inset-0 z-[9995] flex items-end justify-center bg-[#0B1A4D]/40 p-0 sm:items-center sm:p-4">
      <div
        className="relative max-h-[92dvh] w-full max-w-lg overflow-y-auto overscroll-contain rounded-t-2xl border border-slate-200 bg-white p-4 shadow-2xl sm:rounded-2xl sm:p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="profile-complete-title"
      >
        <button
          type="button"
          onClick={dismiss}
          className="absolute end-3 top-3 rounded-full px-2 py-1 text-lg leading-none text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          aria-label={ar ? "إغلاق" : "Fermer"}
        >
          ×
        </button>

        <h2 id="profile-complete-title" className="pe-8 text-xl font-semibold text-[#0B1A4D]">
          {incomplete
            ? ar
              ? "أكملوا بيانات المكتب (اختياري الآن)"
              : "Complétez votre cabinet (optionnel pour l’instant)"
            : ar
              ? "أكملوا ملفكم"
              : "Complétez votre profil"}
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          {incomplete
            ? ar
              ? "يمكنكم استخدام LexHub مباشرة. اسم المكتب والمدينة والهيئة تحسّن ترويسة وثائق Word — يمكن إضافتها لاحقاً من الإعدادات."
              : "Vous pouvez utiliser LexHub tout de suite. Le nom du cabinet, la ville et le barreau améliorent l’en-tête Word — vous pourrez les ajouter plus tard dans Paramètres."
            : ar
              ? "رقم الهاتف اختياري ويحسّن التواصل داخل المكتب."
              : "Le téléphone est optionnel et améliore le contact au sein du cabinet."}
        </p>

        <div className="mt-4 space-y-3">
          {isAdmin && incomplete ? (
            <>
              <Input
                label={ar ? "اسم المكتب (مستحسن)" : "Nom du cabinet (recommandé)"}
                value={cabinetName}
                onChange={(e) => setCabinetName(e.target.value)}
                placeholder={ar ? "مكتب …" : "Cabinet …"}
              />
              <div className="grid gap-3 sm:grid-cols-2">
                <Input
                  label={ar ? "المدينة" : "Ville"}
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Casablanca"
                />
                <Input
                  label={ar ? "الهيئة" : "Barreau"}
                  value={barreau}
                  onChange={(e) => setBarreau(e.target.value)}
                  placeholder="Casablanca"
                />
              </div>
              <Input
                label={ar ? "العنوان" : "Adresse"}
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder={ar ? "الشارع، الحي…" : "Rue, quartier…"}
              />
            </>
          ) : null}
          <Input
            label={ar ? "الهاتف (اختياري)" : "Téléphone (optionnel)"}
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+212 6…"
          />
        </div>

        {msg ? <p className="mt-2 text-sm text-emerald-700">{msg}</p> : null}
        {err ? <p className="mt-2 text-sm text-red-600">{err}</p> : null}

        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:flex-wrap">
          <Button type="button" disabled={busy} onClick={() => void save()} className="w-full sm:min-w-[8rem] sm:w-auto">
            {busy ? "…" : ar ? "حفظ" : "Enregistrer"}
          </Button>
          <Button type="button" variant="outline" onClick={goToSettings} className="w-full sm:w-auto">
            {ar ? "فتح الإعدادات" : "Ouvrir Paramètres"}
          </Button>
          <Button type="button" variant="ghost" onClick={dismiss} className="w-full sm:w-auto">
            {ar ? "لاحقاً — متابعة" : "Plus tard — continuer"}
          </Button>
        </div>
      </div>
    </div>
  );
}
