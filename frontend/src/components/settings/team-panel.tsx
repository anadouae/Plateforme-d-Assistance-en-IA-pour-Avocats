"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Copy, Loader2, RefreshCw, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  api,
  ApiError,
  type JoinCodeInfo,
  type MembershipRequestItem,
  type TeamMember,
} from "@/lib/api";
import { ASSIGNABLE_ROLES, roleLabel } from "@/lib/roles";
import { useLocaleStore, useTranslations } from "@/store/locale";

export function TeamPanel() {
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const t = useTranslations().app.team;
  const [codeInfo, setCodeInfo] = useState<JoinCodeInfo | null>(null);
  const [requests, setRequests] = useState<MembershipRequestItem[]>([]);
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [approveRole, setApproveRole] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [code, reqs, team] = await Promise.all([
        api.getJoinCode(),
        api.getJoinRequests(),
        api.getTeam(),
      ]);
      setCodeInfo(code);
      setRequests(reqs);
      setMembers(team);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function copyCode() {
    if (!codeInfo?.join_code) return;
    try {
      await navigator.clipboard.writeText(codeInfo.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError(t.copyFail);
    }
  }

  async function regenerate() {
    if (!window.confirm(t.regenerateConfirm)) {
      return;
    }
    setBusyId("regen");
    try {
      const next = await api.regenerateJoinCode();
      setCodeInfo(next);
      setMessage(t.regenerated);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur");
    } finally {
      setBusyId(null);
    }
  }

  async function approve(id: string) {
    const role = approveRole[id] || "avocat";
    setBusyId(id);
    setError("");
    try {
      await api.approveJoinRequest(id, role);
      setMessage(t.approved);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur");
    } finally {
      setBusyId(null);
    }
  }

  async function reject(id: string) {
    if (!window.confirm(t.rejectConfirm)) return;
    setBusyId(id);
    try {
      await api.rejectJoinRequest(id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Erreur");
    } finally {
      setBusyId(null);
    }
  }

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
    if (
      !window.confirm(t.removeAccessConfirm.replace("{name}", member.full_name))
    ) {
      return;
    }
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
      {message && (
        <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{message}</p>
      )}
      {error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      <Card className="border-[#B08D3F]/30">
        <CardHeader>
          <CardTitle className="text-base">{t.joinCodeTitle}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-slate-600">{t.joinCodeDesc}</p>
          <div className="flex flex-wrap items-center gap-2">
            <code
              dir="ltr"
              className="rounded-xl border border-[#B08D3F]/40 bg-[#F6EFDD] px-4 py-2.5 font-mono text-lg font-semibold tracking-wider text-[#16233F]"
            >
              {codeInfo?.join_code || "—"}
            </code>
            <Button type="button" size="sm" variant="outline" onClick={() => void copyCode()}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {t.copy}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={busyId === "regen"}
              onClick={() => void regenerate()}
            >
              {busyId === "regen" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {t.regenerate}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t.pendingRequests}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {requests.length === 0 && (
            <p className="text-sm text-slate-400">{t.noRequests}</p>
          )}
          {requests.map((r) => (
            <div
              key={r.id}
              className="flex flex-col gap-3 rounded-xl border border-sanad-border bg-white px-3 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="font-medium text-sanad-navy">{r.full_name}</p>
                <p className="truncate text-xs text-slate-500" dir="ltr">
                  {r.email}
                </p>
                <p className="text-[11px] text-slate-400">
                  {new Date(r.requested_at).toLocaleString(ar ? "ar-MA" : "fr-FR")}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <select
                  className="h-9 rounded-lg border border-sanad-border bg-sanad-cream/40 px-2 text-xs"
                  value={approveRole[r.id] || "avocat"}
                  onChange={(e) =>
                    setApproveRole((prev) => ({ ...prev, [r.id]: e.target.value }))
                  }
                >
                  {ASSIGNABLE_ROLES.map((role) => (
                    <option key={role.value} value={role.value}>
                      {ar ? role.labelAr : role.labelFr}
                    </option>
                  ))}
                </select>
                <Button
                  size="sm"
                  disabled={busyId === r.id}
                  onClick={() => void approve(r.id)}
                >
                  {busyId === r.id ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Check className="h-3.5 w-3.5" />
                  )}
                  {t.approve}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busyId === r.id}
                  onClick={() => void reject(r.id)}
                >
                  <X className="h-3.5 w-3.5" />
                  {t.reject}
                </Button>
              </div>
            </div>
          ))}
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
                  {!m.is_active && (
                    <span className="ms-2 text-[10px] text-red-600">{t.suspended}</span>
                  )}
                </p>
                <p className="truncate text-xs text-slate-500" dir="ltr">
                  {m.email}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <select
                  className="h-8 rounded border border-sanad-border bg-white px-2 text-xs"
                  value={m.role}
                  disabled={busyId === m.id}
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
                {m.is_active && (
                  <button
                    type="button"
                    className="rounded p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                    title={t.removeAccess}
                    onClick={() => void removeAccess(m)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
