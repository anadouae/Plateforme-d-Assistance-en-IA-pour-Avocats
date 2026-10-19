"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Mail, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  api,
  ApiError,
  type BillingEntitlements,
  type CabinetInviteItem,
  type TeamMember,
} from "@/lib/api";
import { ASSIGNABLE_ROLES, roleLabel } from "@/lib/roles";
import { useClientLocale, useTranslations } from "@/store/locale";
import { useAuthStore } from "@/store/auth";
import { useConfirm } from "@/components/ui/confirm-dialog";

export function TeamPanel() {
  const locale = useClientLocale();
  const ar = locale === "ar";
  const t = useTranslations().app.team;
  const user = useAuthStore((s) => s.user);
  const confirm = useConfirm();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("avocat");
  const [inviteBusy, setInviteBusy] = useState(false);
  const [personalInvites, setPersonalInvites] = useState<CabinetInviteItem[]>([]);
  const [ent, setEnt] = useState<BillingEntitlements | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      // Membres d'abord (critique) — timeout court pour ne pas rester en spinner infini.
      const team = await api.getTeam().catch((e) => {
        throw e instanceof ApiError ? e : new ApiError("Erreur équipe", 0);
      });
      setMembers(Array.isArray(team) ? team : []);
    } catch (e) {
      setMembers([]);
      setError(e instanceof ApiError ? e.message : ar ? "تعذّر تحميل الفريق." : "Impossible de charger l’équipe.");
    } finally {
      setLoading(false);
    }
    // Secondaires : ne bloquent jamais l’UI
    void api
      .listTeamInvites()
      .then((invites) => setPersonalInvites(Array.isArray(invites) ? invites : []))
      .catch(() => setPersonalInvites([]));
    void api
      .getBillingEntitlements()
      .then((entitlements) => setEnt(entitlements))
      .catch(() => setEnt(null));
  }, [ar]);

  useEffect(() => {
    void load();
  }, [load]);

  async function changeRole(memberId: string, role: string) {
    setBusyId(memberId);
    try {
      await api.updateTeamMember(memberId, { role });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur");
    } finally {
      setBusyId(null);
    }
  }

  async function removeAccess(member: TeamMember) {
    const ok = await confirm({
      title: t.removeAccessConfirm.replace("{name}", member.full_name),
      tone: "danger",
      requireDeletePhrase: true,
      confirmLabel: ar ? "إزالة" : "Retirer",
    });
    if (!ok) return;
    setBusyId(member.id);
    try {
      await api.updateTeamMember(member.id, { is_active: false });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur");
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-10 text-sm text-slate-500">
        <Loader2 className="h-4 w-4 animate-spin" />
        …
      </div>
    );
  }

  return (
    <div dir={ar ? "rtl" : "ltr"} className="space-y-5">
      {message ? (
        <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{message}</p>
      ) : null}
      {error ? (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : null}

      {ent?.usage ? (
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
          <p className="font-semibold text-[#0B1A4D]">
            {ar ? "مقاعد الخطة" : "Sièges du plan"}{" "}
            <span className="font-normal text-slate-500">
              · {ar ? "محامون" : "Avocats"} {ent.usage.avocats_used ?? 0}/
              {ent.usage.avocats_limit ?? 1} · {ar ? "مساعدون" : "Assistants"}{" "}
              {ent.usage.assistants_used ?? 0}/{ent.usage.assistants_limit ?? 0}
            </span>
          </p>
          <p className="mt-2 text-xs leading-relaxed text-slate-600">
            {ar
              ? "لاستبدال مساعد دون ترقية: أزيلوا وصول المساعد الحالي (إزالة)، ثم ادعوا البديل. عند بلوغ الحد تُرفض الدعوات الجديدة."
              : "Pour remplacer un assistant sans upgrader : retirez l’accès de l’ancien (Retirer), puis invitez le nouveau. À la limite du plan, les nouvelles invitations sont refusées."}
          </p>
        </div>
      ) : null}

      <Card className="border-[#E85A00]/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Mail className="h-5 w-5 text-[#E85A00]" />
            {ar ? "دعوة عضو بالبريد" : "Inviter un membre par email"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-600">
            {ar
              ? "كل الانضمامات تتم عبر دعوة من مسؤول المكتب — رابط شخصي، دخول فوري بدون انتظار."
              : "Toutes les invitations passent par l’admin : email personnel, accès immédiat sans approbation."}
          </p>
          <input
            type="text"
            value={inviteName}
            onChange={(e) => setInviteName(e.target.value)}
            placeholder={ar ? "الاسم (اختياري)" : "Nom du destinataire (optionnel)"}
            className="w-full rounded-lg border border-sanad-stone bg-white px-3 py-2 text-sm"
          />
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="email@cabinet.ma"
            dir="ltr"
            className="w-full rounded-lg border border-sanad-stone bg-white px-3 py-2 text-sm"
          />
          <select
            className="w-full rounded-lg border border-sanad-stone bg-white px-3 py-2 text-sm"
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value)}
          >
            {ASSIGNABLE_ROLES.map((role) => (
              <option key={role.value} value={role.value}>
                {ar ? role.labelAr : role.labelFr}
              </option>
            ))}
          </select>
          <Button
            type="button"
            disabled={inviteBusy || !inviteEmail.trim()}
            onClick={() => {
              if (user?.must_set_password && !user?.auth_via_google) {
                setError(
                  ar
                    ? "أنشئوا كلمة مرور أولاً (الشريط الأصفر) قبل دعوة الفريق."
                    : "Créez d’abord un mot de passe (bandeau jaune) avant d’inviter l’équipe.",
                );
                return;
              }
              setInviteBusy(true);
              setError("");
              void api
                .sendTeamInviteEmail(inviteEmail.trim(), inviteName.trim() || undefined, inviteRole)
                .then((r) => {
                  setMessage(r.message);
                  setInviteEmail("");
                  setInviteName("");
                  return api.listTeamInvites();
                })
                .then((list) => setPersonalInvites(list))
                .catch((e) => setError(e instanceof ApiError ? e.message : "Erreur email"))
                .finally(() => setInviteBusy(false));
            }}
          >
            {inviteBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {ar ? "إرسال الدعوة" : "Envoyer l’invitation"}
          </Button>

          {personalInvites.length > 0 ? (
            <div className="mt-4 space-y-2 border-t border-sanad-border pt-4">
              <p className="text-sm font-semibold text-[#16233F]">
                {ar ? "دعوات في الانتظار" : "Invitations en attente"}
              </p>
              <ul className="space-y-2">
                {personalInvites.map((inv) => (
                  <li
                    key={inv.id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-sanad-stone bg-white px-3 py-2 text-sm"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium" dir="ltr">
                        {inv.email}
                      </p>
                      <p className="text-xs text-slate-500">
                        {roleLabel((inv as { role?: string }).role || "avocat", ar ? "ar" : "fr")}
                        {" · "}
                        {ar ? "تنتهي" : "expire"}{" "}
                        {new Date(inv.expires_at).toLocaleDateString(ar ? "ar-MA" : "fr-FR")}
                      </p>
                      {inv.email_status === "already_on_lexhub" ? (
                        <p className="mt-1 text-[11px] text-amber-800">
                          {ar
                            ? "تنبيه: هذا البريد له حساب LexHub في مكتب آخر — لا يمكن إنشاء حساب ثانٍ (نقل يدوي)."
                            : "Attention : cet email a déjà un compte LexHub ailleurs — pas de 2e compte (transfert manuel)."}
                        </p>
                      ) : null}
                      {inv.email_status === "already_member_same" ? (
                        <p className="mt-1 text-[11px] text-slate-600">
                          {ar ? "عضو بالفعل في مكتبكم." : "Déjà membre de votre cabinet."}
                        </p>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t.members}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {members.map((m) => (
            <div
              key={m.id}
              className="flex flex-col gap-2 rounded-xl border border-sanad-border/70 px-3 py-2.5 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-sanad-navy">
                  {m.full_name}
                  {!m.is_active ? (
                    <span className="ms-2 text-[10px] text-red-600">{t.suspended}</span>
                  ) : null}
                </p>
                <p className="truncate text-xs text-slate-500" dir="ltr">
                  {m.email}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <select
                  className="h-8 rounded border border-sanad-border bg-white px-2 text-xs"
                  value={m.role}
                  disabled={busyId === m.id || !m.is_active}
                  title={!m.is_active ? (ar ? "حساب موقوف — لا يمكن تغيير الدور" : "Compte suspendu — rôle figé") : undefined}
                  onChange={(e) => void changeRole(m.id, e.target.value)}
                >
                  {ASSIGNABLE_ROLES.map((role) => (
                    <option key={role.value} value={role.value}>
                      {ar ? role.labelAr : role.labelFr}
                    </option>
                  ))}
                </select>
                <span className="text-[10px] text-slate-400">
                  {roleLabel(m.role, ar ? "ar" : "fr")}
                </span>
                {m.is_active ? (
                  <button
                    type="button"
                    className="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                    title={t.removeAccess}
                    onClick={() => void removeAccess(m)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
